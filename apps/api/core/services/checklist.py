"""Daily checklist + 24h response window. TODO(Samprada): close window -> NO_RESPONSE."""
from datetime import datetime, timedelta
from core.models import CareEvent


def todays_items(db, patient_id: str, day: datetime | None = None):
    day = day or datetime.utcnow()
    start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return (db.query(CareEvent)
            .filter(CareEvent.patient_id == patient_id,
                    CareEvent.scheduled_at >= start, CareEvent.scheduled_at < end)
            .order_by(CareEvent.scheduled_at).all()), end + timedelta(hours=0)


def close_window(db, now: datetime):
    """Mark items whose 24h window has passed with no response as NO_RESPONSE."""
    cutoff = now - timedelta(hours=24)
    stale = (db.query(CareEvent)
             .filter(CareEvent.scheduled_at < cutoff,
                     CareEvent.status.in_(["UPCOMING", "CURRENT"])).all())
    for e in stale:
        e.status = "NO_RESPONSE"
        e.response_state = "NO_RESPONSE"
    return stale
