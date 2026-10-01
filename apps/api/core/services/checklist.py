"""Daily checklist + 24h response window. TODO(Samprada): close window -> NO_RESPONSE."""
from datetime import datetime, timedelta
from sqlalchemy import or_
from core.models import CareEvent, Patient
from core.services import journey_state


def todays_items(db, patient_id: str, day: datetime | None = None):
    day = day or datetime.utcnow()
    start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return (db.query(CareEvent)
            .filter(CareEvent.patient_id == patient_id,
                    CareEvent.scheduled_at >= start, CareEvent.scheduled_at < end)
            .order_by(CareEvent.scheduled_at).all()), end + timedelta(hours=0)


def close_window(db, now: datetime):
    """Mark items whose 24h window has passed with no response as NO_RESPONSE.
    Patients whose checklist is paused (TRANSFER_OF_CARE, DECEASED) are skipped. After resuming from a paused
    state, events scheduled before the resume are ignored, so the paused period never turns into NO_RESPONSE.
    Any other state change leaves earlier events to be marked as normal."""
    cutoff = now - timedelta(hours=24)
    paused = journey_state.CHECKLIST_PAUSED
    stale = (db.query(CareEvent)
             .join(Patient, Patient.id == CareEvent.patient_id)
             .filter(CareEvent.scheduled_at < cutoff,
                     CareEvent.status.in_(["UPCOMING", "CURRENT"]),
                     Patient.journey_state.notin_(paused),
                     or_(Patient.journey_state_changed_at.is_(None),
                         Patient.previous_journey_state.is_(None),
                         Patient.previous_journey_state.notin_(paused),
                         CareEvent.scheduled_at > Patient.journey_state_changed_at)).all())
    for e in stale:
        e.status = "NO_RESPONSE"
        e.response_state = "NO_RESPONSE"
    return stale
