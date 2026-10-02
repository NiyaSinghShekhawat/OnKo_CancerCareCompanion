from datetime import datetime


def to_dict(obj) -> dict:
    out = {}
    for c in obj.__table__.columns:
        v = getattr(obj, c.name)
        out[c.name] = v.isoformat() if isinstance(v, datetime) else v
    return out


MINIMIZED_EVENT_FIELDS = ("id", "type", "title", "scheduled_at", "status")


def minimized_event(e) -> dict:
    """What a caregiver may see of a CareEvent: no details (doses, instructions), no chapter, no source."""
    full = to_dict(e)
    return {k: full[k] for k in MINIMIZED_EVENT_FIELDS}


def event_for(actor, e) -> dict:
    """Caregivers get the minimized event; doctor, care_team and the patient get the full one."""
    return minimized_event(e) if actor.role == "caregiver" else to_dict(e)
