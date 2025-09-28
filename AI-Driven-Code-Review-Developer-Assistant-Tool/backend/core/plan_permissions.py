"""Plan-based feature access helpers."""

from __future__ import annotations

from typing import Dict, Set

from models.user import SubscriptionTier


_FEATURE_MATRIX: Dict[str, Set[SubscriptionTier]] = {
    'analytics': {SubscriptionTier.PROFESSIONAL, SubscriptionTier.ENTERPRISE},
    'rag': {SubscriptionTier.PROFESSIONAL, SubscriptionTier.ENTERPRISE},
}


def has_feature_access(tier: SubscriptionTier, feature_key: str) -> bool:
    """Return True if the plan tier can use a gated feature."""
    allowed = _FEATURE_MATRIX.get(feature_key, set())
    return tier in allowed


__all__ = ["has_feature_access"]
