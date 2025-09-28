from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import timedelta


@dataclass(frozen=True)
class Plan:
    key: str
    name: str
    monthly_price_cents: int
    monthly_analysis_limit: int  # -1 for unlimited
    features: List[str]
    trial_days: int = 0
    stripe_price_id: Optional[str] = None  # Placeholder for real Stripe price IDs

    @property
    def is_unlimited(self) -> bool:
        return self.monthly_analysis_limit < 0


PLANS: Dict[str, Plan] = {
    "free": Plan(
        key="free",
        name="Free",
        monthly_price_cents=0,
        monthly_analysis_limit=5,
        features=[
            "5 monthly analyses",
            "Basic code review",
            "Community support",
        ],
    ),
    "professional": Plan(
        key="professional",
        name="Professional",
        monthly_price_cents=2900,
        monthly_analysis_limit=-1,
        features=[
            "Unlimited analyses",
            "PR reviews",
            "Test generation",
            "Priority support",
            "Advanced AI models",
            "Basic analytics",
        ],
        trial_days=14,
    ),
    "enterprise": Plan(
        key="enterprise",
        name="Enterprise",
        monthly_price_cents=9900,
        monthly_analysis_limit=-1,
        features=[
            "Unlimited analyses",
            "Team management",
            "Custom rules & policies",
            "Dedicated support & SLA",
            "Advanced security & SSO",
            "Full analytics suite",
        ],
        trial_days=21,
    ),
}


def get_plan(key: str) -> Plan:
    return PLANS[key]


def list_public_plans() -> Dict[str, dict]:
    return {
        k: {
            "name": v.name,
            "price_cents": v.monthly_price_cents,
            "monthly_limit": v.monthly_analysis_limit,
            "features": v.features,
            "trial_days": v.trial_days,
        }
        for k, v in PLANS.items() if k != "enterprise" or True
    }


def remaining_quota(plan_key: str, used: int) -> int:
    plan = get_plan(plan_key)
    if plan.is_unlimited:
        return -1
    return max(plan.monthly_analysis_limit - used, 0)


__all__ = ["Plan", "PLANS", "get_plan", "list_public_plans", "remaining_quota"]
