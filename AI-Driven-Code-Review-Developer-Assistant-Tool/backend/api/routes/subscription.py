from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
import stripe
from datetime import datetime, timedelta

from core.config import get_settings
from models.user import User, SubscriptionTier
from sqlalchemy.orm import Session
from core.db import get_db
from core.plan_config import list_public_plans, get_plan, remaining_quota
from core.security import verify_token
from datetime import timezone
from core.payment_security import payment_security

router = APIRouter()

class SubscriptionRequest(BaseModel):
    tier: str
    payment_method_id: str

class WebhookRequest(BaseModel):
    type: str
    data: Dict[str, Any]

settings = get_settings()
stripe.api_key = getattr(settings, 'stripe_secret_key', 'sk_test_...')

def _current_user(request: Request, db: Session) -> Optional[User]:
    auth_header = request.headers.get("Authorization") or request.headers.get('authorization')
    if not auth_header or not auth_header.lower().startswith('bearer '):
        return None
    token = auth_header.split(' ', 1)[1].strip()
    payload = verify_token(token)
    if not payload:
        return None
    username = payload.get('sub')
    if not username:
        return None
    return db.query(User).filter(User.username == username).first()

@router.get("/plans")
async def get_pricing_plans():
    return {"plans": list_public_plans()}

@router.post("/create-payment-intent")
async def create_payment_intent(payload: SubscriptionRequest):
    """Create a payment intent for subscription."""
    try:
        plan = get_plan(payload.tier)
        if plan.monthly_price_cents <= 0:
            raise HTTPException(status_code=400, detail="Selected plan does not require payment")

        intent = payment_security.create_secure_payment_intent(
            amount=plan.monthly_price_cents,
            currency='usd',
            metadata={
                'subscription_tier': payload.tier,
                'plan_name': plan.name,
            }
        )

        if not intent:
            raise HTTPException(status_code=500, detail="Unable to create payment intent")

        return {
            'client_secret': intent.client_secret,
            'amount': plan.monthly_price_cents,
            'currency': 'usd'
        }

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment processing failed: {str(e)}")

@router.post("/create-subscription")
async def create_subscription(
    payload: SubscriptionRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new subscription."""
    try:
        user = _current_user(request, db)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")

        plan = get_plan(payload.tier)
        if plan.monthly_price_cents <= 0:
            raise HTTPException(status_code=400, detail="Selected plan does not require billing")

        subscription = payment_security.create_secure_subscription(
            plan_name=plan.name,
            amount_cents=plan.monthly_price_cents,
            payment_method_id=payload.payment_method_id,
            customer_email=user.email,
            metadata={
                'subscription_tier': payload.tier,
                'user_id': str(user.id),
            }
        )

        if not subscription or not subscription.latest_invoice:
            raise HTTPException(status_code=500, detail="Failed to provision subscription")

        user.subscription_tier = SubscriptionTier[plan.key.upper()] if plan.key != 'free' else SubscriptionTier.FREE
        user.subscription_id = subscription.id
        user.stripe_customer_id = subscription.customer if isinstance(subscription.customer, str) else subscription.customer.get('id')  # type: ignore[attr-defined]
        user.plan_started_at = datetime.utcnow()
        user.plan_changed_at = datetime.utcnow()
        user.subscription_ends_at = None
        db.commit()

        payment_intent = subscription.latest_invoice.payment_intent  # type: ignore[attr-defined]
        client_secret = payment_intent.client_secret if payment_intent else None

        return {
            'subscription_id': subscription.id,
            'client_secret': client_secret,
            'status': subscription.status
        }

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Subscription creation failed: {str(e)}")

@router.post("/start-trial")
async def start_trial(tier: str = "professional", request: Request = None, db: Session = Depends(get_db)):
    try:
        user = _current_user(request, db)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
        plan = get_plan(tier)
        if plan.trial_days <= 0:
            raise HTTPException(status_code=400, detail="Selected plan has no trial")
        if user.trial_ends_at and user.trial_ends_at > datetime.utcnow():
            raise HTTPException(status_code=400, detail="Trial already active")
        user.trial_ends_at = datetime.utcnow() + timedelta(days=plan.trial_days)
        user.plan_started_at = datetime.utcnow()
        user.plan_changed_at = datetime.utcnow()
        user.subscription_tier = SubscriptionTier[plan.key.upper()] if plan.key != 'free' else SubscriptionTier.FREE
        db.commit()
        return {
            "message": f"{plan.trial_days}-day trial started for {plan.name}",
            "trial_ends_at": user.trial_ends_at.isoformat(),
            "features": plan.features,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trial creation failed: {str(e)}")

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    etype = event['type']
    data_obj = event['data']['object']

    def find_user_by_stripe_customer(customer_id: str) -> Optional[User]:
        return db.query(User).filter(User.stripe_customer_id == customer_id).first()

    try:
        if etype == 'customer.subscription.created' or etype == 'customer.subscription.updated':
            customer_id = data_obj.get('customer')
            plan_id = data_obj.get('items', {}).get('data', [{}])[0].get('plan', {}).get('nickname') or ''
            status = data_obj.get('status')
            user = find_user_by_stripe_customer(customer_id)
            if user:
                # Map nickname loosely to internal plan keys
                normalized = plan_id.lower().replace(' ', '')
                if normalized in ('professional', 'pro'):
                    user.subscription_tier = SubscriptionTier.PROFESSIONAL
                elif normalized in ('enterprise',):
                    user.subscription_tier = SubscriptionTier.ENTERPRISE
                user.subscription_id = data_obj.get('id')
                user.plan_changed_at = datetime.utcnow()
                if not user.plan_started_at:
                    user.plan_started_at = datetime.utcnow()
                # Clear cancellation marker if reactivated
                user.subscription_ends_at = None
                db.commit()
        elif etype == 'invoice.payment_succeeded':
            invoice = data_obj
            customer_id = invoice.get('customer')
            user = find_user_by_stripe_customer(customer_id)
            if user:
                # Extend subscription (placeholder: add 30 days)
                user.subscription_ends_at = None
                db.commit()
        elif etype == 'customer.subscription.deleted':
            customer_id = data_obj.get('customer')
            user = find_user_by_stripe_customer(customer_id)
            if user:
                user.subscription_tier = SubscriptionTier.FREE
                user.subscription_ends_at = datetime.utcnow()
                db.commit()
        elif etype == 'payment_intent.payment_failed':
            # Could mark account in grace period
            pass
    except Exception as e:
        # Do not fail webhook delivery for internal errors unless critical
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")

    return {"received": True}

@router.get("/usage")
async def get_usage_stats(request: Request, db: Session = Depends(get_db)):
    user = _current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    plan_key = user.subscription_tier.value
    plan = get_plan(plan_key)
    remaining = remaining_quota(plan_key, user.monthly_analyses_used or 0)
    trial_days_remaining = 0
    if user.trial_ends_at and user.trial_ends_at > datetime.utcnow():
        trial_days_remaining = (user.trial_ends_at - datetime.utcnow()).days
    return {
        "current_tier": plan_key,
        "monthly_analyses_used": user.monthly_analyses_used,
        "monthly_limit": plan.monthly_analysis_limit,
        "remaining": remaining,
        "total_analyses": user.total_analyses,
        "trial_days_remaining": trial_days_remaining,
        "features": plan.features,
    }

@router.post("/upgrade")
async def upgrade_subscription(tier: str, request: Request, db: Session = Depends(get_db)):
    try:
        user = _current_user(request, db)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
        if not user.email_verified_at:
            raise HTTPException(status_code=403, detail="Email verification required before upgrading plan")
        plan = get_plan(tier)
        # Placeholder billing logic - integrate Stripe subscription update
        if user.subscription_tier.value == tier:
            return {"message": "Already on requested plan"}
        user.subscription_tier = SubscriptionTier[tier.upper()] if tier != 'free' else SubscriptionTier.FREE
        user.plan_changed_at = datetime.utcnow()
        if not user.plan_started_at:
            user.plan_started_at = datetime.utcnow()
        db.commit()
        return {"message": f"Upgraded to {plan.name}", "features": plan.features}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upgrade failed: {str(e)}")

@router.post("/cancel")
async def cancel_subscription(request: Request, db: Session = Depends(get_db)):
    try:
        user = _current_user(request, db)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
        # Placeholder: mark downgrade to free at period end
        user.subscription_tier = SubscriptionTier.FREE
        user.subscription_ends_at = datetime.utcnow()
        db.commit()
        return {"message": "Subscription cancelled", "effective": user.subscription_ends_at.isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cancellation failed: {str(e)}")

@router.get("/status")
async def subscription_status(request: Request, db: Session = Depends(get_db)):
    user = _current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    plan_key = user.subscription_tier.value
    plan = get_plan(plan_key)
    trial_active = user.trial_ends_at and user.trial_ends_at > datetime.utcnow()
    return {
        "tier": plan_key,
        "trial_active": bool(trial_active),
        "trial_ends_at": user.trial_ends_at.isoformat() if user.trial_ends_at else None,
        "plan_started_at": user.plan_started_at.isoformat() if user.plan_started_at else None,
        "plan_changed_at": user.plan_changed_at.isoformat() if user.plan_changed_at else None,
        "subscription_ends_at": user.subscription_ends_at.isoformat() if user.subscription_ends_at else None,
        "unlimited": plan.is_unlimited,
        "features": plan.features,
    }

@router.get("/billing-portal")
async def create_billing_portal():
    """Create a billing portal session."""
    try:
        # TODO: Get customer ID from database
        customer_id = "cus_example"

        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url='http://localhost:3000/dashboard',
        )

        return {'url': session.url}

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Billing portal creation failed: {str(e)}")
