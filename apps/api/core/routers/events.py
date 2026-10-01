from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.db import get_db
from core.auth import get_actor, require, require_patient_access
from core.models import CareEvent, Patient
from core.serialize import to_dict
from core.services import audit, checklist, attention, journey_state
from core import seed

router = APIRouter(tags=["events"])


class StatusIn(BaseModel):
    status: str           # COMPLETED | REPORTED_MISSED | ...
    source: str = "patient"


@router.patch("/events/{event_id}/status")
def set_status(event_id: str, body: StatusIn, db=Depends(get_db), actor=Depends(get_actor)):
    """Also called by whatsapp/webhook.py with Actor("patient", <that patient>), which passes the check."""
    e = db.get(CareEvent, event_id)
    if not e:
        raise HTTPException(404, "Event not found")
    require_patient_access(actor, e.patient_id, db)
    before = e.status
    e.status = body.status
    e.response_state = body.status if body.status in {"COMPLETED", "REPORTED_MISSED", "CONFLICTING"} else e.response_state
    e.responded_at = datetime.utcnow()
    if body.status == "REPORTED_MISSED":
        attention.raise_missed(db, db.get(Patient, e.patient_id), e)   # no-op for PALLIATIVE
    audit.log(db, actor, "event_status", "care_event", e.id, {"status": before}, {"status": body.status})
    db.commit()
    return to_dict(e)


@router.get("/patients/{pid}/checklist/today")
def today(pid: str, db=Depends(get_db), actor=Depends(get_actor)):
    require_patient_access(actor, pid, db)
    items, closes = checklist.todays_items(db, pid)
    p = db.get(Patient, pid)
    paused = bool(p) and journey_state.checklist_paused(p.journey_state)
    return {"patient_id": pid, "date": datetime.utcnow().date().isoformat(),
            "items": [] if paused else [to_dict(i) for i in items],
            "window_closes_at": closes.isoformat(), "sent": False,
            "paused": paused, "reason": f"Journey state {p.journey_state}" if paused else None}


@router.post("/demo/advance-day")
def advance_day(db=Depends(get_db), actor=Depends(get_actor)):
    require(actor, "doctor")   # changes every patient's events and attention, like /demo/reset
    now = datetime.utcnow()
    stale = checklist.close_window(db, now)
    for p in db.query(Patient).all():
        attention.recompute_for_patient(db, p, now)
    db.commit()
    return {"marked_no_response": len(stale)}


@router.post("/demo/reset")
def reset_demo(db=Depends(get_db), actor=Depends(get_actor)):
    require(actor, "doctor")
    seed.run(db)
    db.commit()
    return {"reset": True}
