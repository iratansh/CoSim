import hmac
import hashlib
import logging
from typing import Dict, Any, Optional
import stripe
from datetime import datetime, timedelta
import json
import secrets
from dataclasses import dataclass
import os  # Added missing import used in PCICompliance.validate_pci_environment

from core.config import get_settings
from core.database_security import db_security, AuditLog

settings = get_settings()
logger = logging.getLogger(__name__)

# Configure Stripe with security settings
stripe.api_key = settings.stripe_secret_key
stripe.max_network_retries = 2
stripe.api_version = "2023-10-16"  # Use specific API version for consistency

@dataclass
class PaymentSecurityConfig:
    """Payment security configuration."""
    max_payment_amount: int = 100000  # $1000 in cents
    max_daily_payments: int = 10
    max_monthly_payments: int = 100
    suspicious_amount_threshold: int = 50000  # $500 in cents
    webhook_tolerance: int = 300  # 5 minutes

class PaymentSecurity:
    """Comprehensive payment security implementation."""

    def __init__(self):
        self.config = PaymentSecurityConfig()
        self.blocked_cards = set()
        self.suspicious_transactions = {}

    def validate_payment_amount(self, amount: int, currency: str = 'usd') -> tuple[bool, str]:
        """Validate payment amount for security."""
        if amount <= 0:
            return False, "Invalid payment amount"

        if amount > self.config.max_payment_amount:
            return False, f"Payment amount exceeds maximum allowed ({self.config.max_payment_amount/100})"

        # Flag suspicious amounts
        if amount >= self.config.suspicious_amount_threshold:
            logger.warning(f"Large payment attempt: ${amount/100}")
            AuditLog.log_security_event(
                "large_payment_attempt",
                "medium",
                {"amount": amount, "currency": currency}
            )

        return True, "Valid amount"

    def validate_payment_frequency(self, user_id: int, time_window: str = 'daily') -> tuple[bool, str]:
        """Check payment frequency limits."""
        # In production, implement with Redis or database
        # This is a simplified version

        now = datetime.utcnow()

        if time_window == 'daily':
            # Check daily limit
            daily_count = self._get_payment_count(user_id, now - timedelta(days=1))
            if daily_count >= self.config.max_daily_payments:
                return False, f"Daily payment limit exceeded ({self.config.max_daily_payments})"

        elif time_window == 'monthly':
            # Check monthly limit
            monthly_count = self._get_payment_count(user_id, now - timedelta(days=30))
            if monthly_count >= self.config.max_monthly_payments:
                return False, f"Monthly payment limit exceeded ({self.config.max_monthly_payments})"

        return True, "Frequency check passed"

    def _get_payment_count(self, user_id: int, since: datetime) -> int:
        """Get payment count for user since specific time."""
        # Implement with actual database query
        return 0  # Placeholder

    def verify_stripe_webhook(self, payload: bytes, signature: str) -> tuple[bool, Optional[Dict]]:
        """Verify Stripe webhook signature for security."""
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.stripe_webhook_secret,
                tolerance=self.config.webhook_tolerance
            )
            return True, event
        except ValueError:
            logger.error("Invalid Stripe webhook payload")
            return False, None
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid Stripe webhook signature")
            AuditLog.log_security_event(
                "invalid_webhook_signature",
                "high",
                {"signature": signature[:20] + "..."}
            )
            return False, None

    def validate_payment_method(self, payment_method_id: str) -> tuple[bool, str]:
        """Validate Stripe payment method."""
        try:
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)

            # Check if card is blocked
            if payment_method.type == 'card':
                card = payment_method.card
                card_fingerprint = card.fingerprint

                if card_fingerprint in self.blocked_cards:
                    return False, "Payment method blocked"

                # Additional security checks
                if card.funding == 'prepaid':
                    logger.warning(f"Prepaid card used: {card_fingerprint}")

                # Check for suspicious patterns
                if self._is_suspicious_card(card):
                    self._flag_suspicious_transaction(payment_method_id)
                    return False, "Payment method flagged for review"

            return True, "Payment method valid"

        except stripe.error.StripeError as e:
            logger.error(f"Stripe validation error: {e}")
            return False, "Payment method validation failed"

    def _is_suspicious_card(self, card) -> bool:
        """Check if card shows suspicious patterns."""
        suspicious_indicators = [
            card.country != 'US' and card.funding == 'prepaid',  # Foreign prepaid cards
            len(card.exp_year) != 4,  # Invalid year format
        ]

        return any(suspicious_indicators)

    def _flag_suspicious_transaction(self, payment_method_id: str):
        """Flag transaction for manual review."""
        self.suspicious_transactions[payment_method_id] = {
            'timestamp': datetime.utcnow().isoformat(),
            'flagged_for': 'suspicious_card_pattern'
        }

        AuditLog.log_security_event(
            "suspicious_payment_method",
            "medium",
            {"payment_method_id": payment_method_id}
        )

    def create_secure_payment_intent(
        self,
        amount: int,
        currency: str,
        customer_id: Optional[str] = None,
        metadata: Dict[str, str] = None
    ) -> Optional[stripe.PaymentIntent]:
        """Create payment intent with security measures."""
        try:
            # Validate amount
            is_valid, message = self.validate_payment_amount(amount, currency)
            if not is_valid:
                raise ValueError(message)

            # Add security metadata
            secure_metadata = {
                'created_by': 'codegenius_api',
                'security_version': '1.0',
                'timestamp': datetime.utcnow().isoformat(),
                **(metadata or {})
            }

            # Create payment intent with security settings
            create_kwargs = dict(
                amount=amount,
                currency=currency,
                metadata=secure_metadata,
                confirmation_method='manual',
                capture_method='automatic',
                # Security settings
                receipt_email=None,  # Don't auto-send receipts
                setup_future_usage='off_session',  # Allow future payments
            )

            if customer_id:
                create_kwargs['customer'] = customer_id

            intent = stripe.PaymentIntent.create(**create_kwargs)

            # Log payment creation
            AuditLog.log_security_event(
                "payment_intent_created",
                "info",
                {
                    "intent_id": intent.id,
                    "amount": amount,
                    "customer_id": customer_id
                }
            )

            return intent

        except stripe.error.StripeError as e:
            logger.error(f"Payment intent creation failed: {e}")
            AuditLog.log_security_event(
                "payment_intent_failed",
                "medium",
                {"error": str(e), "amount": amount}
            )
            return None

    def process_secure_payment(
        self,
        payment_intent_id: str,
        payment_method_id: str,
        user_id: int
    ) -> tuple[bool, str, Optional[Dict]]:
        """Process payment with comprehensive security checks."""
        try:
            # Validate payment method
            is_valid, message = self.validate_payment_method(payment_method_id)
            if not is_valid:
                return False, message, None

            # Check payment frequency
            is_valid, message = self.validate_payment_frequency(user_id)
            if not is_valid:
                return False, message, None

            # Confirm payment intent
            intent = stripe.PaymentIntent.confirm(
                payment_intent_id,
                payment_method=payment_method_id
            )

            # Log successful payment
            AuditLog.log_user_action(
                user_id,
                "payment_processed",
                "subscription",
                {
                    "intent_id": payment_intent_id,
                    "amount": intent.amount,
                    "status": intent.status
                }
            )

            return True, "Payment processed successfully", {
                "intent_id": intent.id,
                "status": intent.status,
                "amount": intent.amount
            }

        except stripe.error.CardError as e:
            # Card was declined
            error_msg = e.user_message or "Card declined"
            logger.warning(f"Card declined: {e}")

            # Track declined attempts
            self._track_declined_payment(user_id, payment_method_id, str(e))

            return False, error_msg, None

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error during payment: {e}")
            return False, "Payment processing failed", None

    def _track_declined_payment(self, user_id: int, payment_method_id: str, reason: str):
        """Track declined payments for fraud detection."""
        AuditLog.log_security_event(
            "payment_declined",
            "medium",
            {
                "user_id": user_id,
                "payment_method_id": payment_method_id,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    def encrypt_payment_data(self, payment_data: Dict[str, Any]) -> str:
        """Encrypt sensitive payment data for storage."""
        # Remove sensitive fields before encryption
        safe_data = {
            k: v for k, v in payment_data.items()
            if k not in ['card_number', 'cvv', 'exp_month', 'exp_year']
        }

        return db_security.encrypt_sensitive_data(json.dumps(safe_data))

    def handle_webhook_securely(self, event: Dict[str, Any]) -> bool:
        """Handle Stripe webhook events securely."""
        event_type = event['type']
        event_data = event['data']['object']

        try:
            if event_type == 'payment_intent.succeeded':
                self._handle_successful_payment(event_data)

            elif event_type == 'payment_intent.payment_failed':
                self._handle_failed_payment(event_data)

            elif event_type == 'customer.subscription.deleted':
                self._handle_subscription_cancellation(event_data)

            elif event_type == 'invoice.payment_failed':
                self._handle_invoice_failure(event_data)

            # Log webhook processing
            AuditLog.log_security_event(
                "webhook_processed",
                "info",
                {"event_type": event_type, "event_id": event['id']}
            )

            return True

        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            AuditLog.log_security_event(
                "webhook_error",
                "high",
                {"event_type": event_type, "error": str(e)}
            )
            return False

    def _handle_successful_payment(self, payment_intent):
        """Handle successful payment webhook."""
        logger.info(f"Payment succeeded: {payment_intent['id']}")
        # Update user subscription status

    def _handle_failed_payment(self, payment_intent):
        """Handle failed payment webhook."""
        logger.warning(f"Payment failed: {payment_intent['id']}")
        # Notify user and handle grace period

    def _handle_subscription_cancellation(self, subscription):
        """Handle subscription cancellation webhook."""
        logger.info(f"Subscription cancelled: {subscription['id']}")
        # Update user access

    def _handle_invoice_failure(self, invoice):
        """Handle invoice payment failure."""
        logger.warning(f"Invoice payment failed: {invoice['id']}")
        # Handle dunning process

    def generate_idempotency_key(self, user_id: int, amount: int) -> str:
        """Generate idempotency key for payment deduplication."""
        base_string = f"{user_id}:{amount}:{datetime.utcnow().date()}"
        return hashlib.sha256(base_string.encode()).hexdigest()

    def block_payment_method(self, payment_method_id: str, reason: str):
        """Block a payment method for security reasons."""
        # In production, store in database
        self.blocked_cards.add(payment_method_id)

        AuditLog.log_security_event(
            "payment_method_blocked",
            "high",
            {"payment_method_id": payment_method_id, "reason": reason}
        )

    def is_test_environment(self) -> bool:
        """Check if running in test environment."""
        return settings.stripe_secret_key.startswith('sk_test_')

    def create_secure_subscription(
        self,
        plan_name: str,
        amount_cents: int,
        payment_method_id: str,
        currency: str = 'usd',
        customer_email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> stripe.Subscription:
        """Provision a Stripe subscription with security controls."""
        is_valid, message = self.validate_payment_amount(amount_cents, currency)
        if not is_valid:
            raise ValueError(message)

        secure_metadata = {
            'plan_name': plan_name,
            'security_version': '1.0',
            'timestamp': datetime.utcnow().isoformat(),
        }
        if metadata:
            secure_metadata.update(metadata)

        customer_kwargs = {
            'payment_method': payment_method_id,
            'invoice_settings': {'default_payment_method': payment_method_id},
        }
        if customer_email:
            customer_kwargs['email'] = customer_email

        customer = stripe.Customer.create(**customer_kwargs)

        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{
                'price_data': {
                    'currency': currency,
                    'product_data': {
                        'name': plan_name,
                    },
                    'unit_amount': amount_cents,
                    'recurring': {
                        'interval': 'month',
                    },
                },
            }],
            payment_behavior='default_incomplete',
            payment_settings={'save_default_payment_method': 'on_subscription'},
            expand=['latest_invoice.payment_intent'],
            metadata=secure_metadata,
        )

        AuditLog.log_security_event(
            "subscription_created",
            "info",
            {
                'subscription_id': subscription.id,
                'plan': plan_name,
                'customer_id': customer.id,
                'amount': amount_cents,
            }
        )

        return subscription

# Initialize payment security
payment_security = PaymentSecurity()

class PCICompliance:
    """PCI DSS compliance utilities."""

    @staticmethod
    def mask_card_number(card_number: str) -> str:
        """Mask card number for PCI compliance."""
        if not card_number:
            return ""

        # Remove spaces and non-digits
        digits = ''.join(filter(str.isdigit, card_number))

        if len(digits) < 8:
            return '*' * len(digits)

        # Show only first 6 and last 4 digits (PCI compliant)
        return digits[:6] + '*' * (len(digits) - 10) + digits[-4:]

    @staticmethod
    def validate_pci_environment():
        """Validate PCI compliance requirements."""
        issues = []

        # Check HTTPS enforcement
        if not settings.debug and not os.getenv('FORCE_HTTPS'):
            issues.append("HTTPS not enforced in production")

        # Check encryption
        if not os.getenv('DATABASE_ENCRYPTION_KEY'):
            issues.append("Database encryption not configured")

        # Check logging
        if not settings.debug:  # In production
            if not os.getenv('SECURITY_LOG_LEVEL'):
                issues.append("Security logging not configured")

        return issues

# Fraud detection patterns
class FraudDetection:
    """Simple fraud detection patterns."""

    @staticmethod
    def detect_velocity_fraud(user_id: int, transaction_count: int, time_window_hours: int = 1) -> bool:
        """Detect velocity-based fraud."""
        # Check if user made too many transactions in short time
        if time_window_hours == 1 and transaction_count > 5:
            return True
        if time_window_hours == 24 and transaction_count > 20:
            return True
        return False

    @staticmethod
    def detect_amount_fraud(amounts: list[int]) -> bool:
        """Detect suspicious payment amounts."""
        if not amounts:
            return False

        # Check for round numbers (potential testing)
        round_numbers = sum(1 for amount in amounts if amount % 1000 == 0)
        if round_numbers / len(amounts) > 0.8:  # 80% are round numbers
            return True

        # Check for escalating amounts (card testing)
        if len(amounts) >= 3:
            sorted_amounts = sorted(amounts)
            if sorted_amounts == amounts:  # Perfectly ascending
                return True

        return False
