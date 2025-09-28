from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from core.db import get_db
from models.analysis_event import AnalysisEvent
from models.user import User
from core.security import verify_token
from core.plan_permissions import has_feature_access

router = APIRouter()


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


@router.get("/summary")
async def analytics_summary(request: Request, db: Session = Depends(get_db)):
    user = _current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    if not has_feature_access(user.subscription_tier, 'analytics'):
        raise HTTPException(status_code=403, detail="Upgrade required for analytics")

    total_events = db.query(AnalysisEvent).count()
    now = datetime.utcnow()
    last_7 = now - timedelta(days=7)
    last_30 = now - timedelta(days=30)
    events_7 = db.query(AnalysisEvent).filter(AnalysisEvent.created_at >= last_7).count()
    events_30 = db.query(AnalysisEvent).filter(AnalysisEvent.created_at >= last_30).count()
    users_with_events = db.query(AnalysisEvent.user_id).distinct().count()
    return {
        "total_events": total_events,
        "events_last_7_days": events_7,
        "events_last_30_days": events_30,
        "active_users": users_with_events,
    }


@router.get("/usage")
async def analytics_usage(request: Request, days: int = 14, db: Session = Depends(get_db)):
    user = _current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    if not has_feature_access(user.subscription_tier, 'analytics'):
        raise HTTPException(status_code=403, detail="Upgrade required for analytics")

    if days > 90:
        days = 90
    now = datetime.utcnow()
    start = now - timedelta(days=days)
    # Simple aggregation (can be optimized with GROUP BY date)
    rows = db.query(AnalysisEvent).filter(AnalysisEvent.created_at >= start).all()
    buckets: Dict[str, int] = {}
    for r in rows:
        d = r.created_at.date().isoformat() if r.created_at else now.date().isoformat()
        buckets[d] = buckets.get(d, 0) + 1
    # Fill missing days
    ordered = []
    for i in range(days + 1):
        day = (start + timedelta(days=i)).date().isoformat()
        ordered.append({"date": day, "count": buckets.get(day, 0)})
    return {"range_days": days, "data": ordered}


@router.get("/user")
async def analytics_user(request: Request, db: Session = Depends(get_db)):
    user = _current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    if not has_feature_access(user.subscription_tier, 'analytics'):
        raise HTTPException(status_code=403, detail="Upgrade required for analytics")
    events = db.query(AnalysisEvent).filter(AnalysisEvent.user_id == user.id).order_by(AnalysisEvent.created_at.desc()).limit(50).all()
    total = db.query(AnalysisEvent).filter(AnalysisEvent.user_id == user.id).count()
    by_type: Dict[str, int] = {}
    for e in events:
        by_type[e.type] = by_type.get(e.type, 0) + 1
    return {
        "total_events": total,
        "recent": [
            {
                "id": e.id,
                "type": e.type,
                "language": e.language,
                "success": e.success,
                "duration_ms": e.duration_ms,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            } for e in events
        ],
        "by_type": by_type,
    }
