from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum
from models.base import Base
from sqlalchemy.sql import func
import enum


class SubscriptionTier(enum.Enum):
    FREE = "free"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    company = Column(String(100))

    # Subscription info
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    stripe_customer_id = Column(String(100))
    subscription_id = Column(String(100))
    trial_ends_at = Column(DateTime)
    subscription_ends_at = Column(DateTime)
    plan_started_at = Column(DateTime)
    plan_changed_at = Column(DateTime)

    # Usage tracking
    monthly_analyses_used = Column(Integer, default=0)
    total_analyses = Column(Integer, default=0)

    # Profile
    github_username = Column(String(100))
    avatar_url = Column(String(255))

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    email_verified_at = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    @property
    def is_premium(self):
        return self.subscription_tier in [SubscriptionTier.PROFESSIONAL, SubscriptionTier.ENTERPRISE]

    @property
    def monthly_limit(self):
        limits = {
            SubscriptionTier.FREE: 5,
            SubscriptionTier.PROFESSIONAL: -1,  # Unlimited
            SubscriptionTier.ENTERPRISE: -1,   # Unlimited
        }
        return limits.get(self.subscription_tier, 5)

    def can_analyze(self):
        if self.subscription_tier == SubscriptionTier.FREE:
            return self.monthly_analyses_used < 5
        return True