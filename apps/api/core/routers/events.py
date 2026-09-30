from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.db import get_db
from core.auth import get_actor
from core.models import CareEvent, Patient
from core.serialize import to_dict
from core.services import audit, checklist, attention

router = APIRouter(tags=["events"])


class StatusIn(BaseModel):
    status: str           # COMPLETED | REPORTED_MISSED | ...
    source: str = "patient"


@router.patch("/events/{event_id}/status")
def set_status(event_id: str, body: StatusIn, db=Depends(get_db), actor=Depends(get_actor)):
    e = db.get(CareEvent, event_id)
    if not e:
        raise HTTPException(404, "Event not found")
    before = e.status
    e.status = body.status
    e.response_state = body.status if body.status in {"COMPLETED", "REPORTED_MISSED", "CONFLICTING"} else e.response_state
    e.responded_at = datetime.utcnow()
    if body.status == "REPORTED_MISSED" and e.type in {"MEDICATION", "TREATMENT"}:
        p = db.get(Patient, e.patient_id)
        attention.raise_item(db, p, "NEEDS_REVIEW",
                             f"{e.type.title()} reported missed: {e.title}, {e.scheduled_at:%d %b}")
    audit.log(db, actor, "event_status", "care_event", e.id, {"status": before}, {"status": body.status})
    db.commit()
    return to_dict(e)


@router.get("/patients/{pid}/checklist/today")
def today(pid: str, db=Depends(get_db)):
    items, closes = checklist.todays_items(db, pid)
    return {"patient_id": pid, "date": datetime.utcnow().date().isoformat(),
            "items": [to_dict(i) for i in items], "window_closes_at": closes.isoformat(), "sent": False}


@router.post("/demo/advance-day")
def advance_day(db=Depends(get_db)):
    now = datetime.utcnow()
    stale = checklist.close_window(db, now)
    for p in db.query(Patient).all():
        attention.recompute_for_patient(db, p, now)
    db.commit()
    return {"marked_no_response": len(stale)}
