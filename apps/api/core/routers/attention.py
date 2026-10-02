from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.db import get_db
from core.auth import STAFF, get_actor, require
from core.models import AttentionItem, Patient, PatientQuery, Report, CareEvent
from core.serialize import to_dict
from core.services import audit

router = APIRouter(tags=["attention"])
ORDER = {"SOS": 0, "NEEDS_REVIEW": 1, "QUERY": 2, "FOLLOW_UP": 3}


@router.get("/attention")
def list_attention(db=Depends(get_db), actor=Depends(get_actor)):
    require(actor, *STAFF)
    # The attention queue is an active work queue. HANDLED/CLOSED items remain in the DB
    # for Patient 360 history, but no longer occupy the live queue.
    items = db.query(AttentionItem).filter(AttentionItem.status.in_(["PENDING", "ACKNOWLEDGED"])).all()
    items.sort(key=lambda i: (ORDER.get(i.label, 9), i.created_at))
    return [to_dict(i) for i in items]


class AttentionUpdate(BaseModel):
    status: str
    assigned_to: str | None = None


@router.patch("/attention/{aid}")
def update_attention(aid: str, body: AttentionUpdate, db=Depends(get_db), actor=Depends(get_actor)):
    require(actor, *STAFF)
    a = db.get(AttentionItem, aid)
    if not a:
        raise HTTPException(404, "Not found")
    before = {"status": a.status, "assigned_to": a.assigned_to}
    a.status = body.status
    fields_set = body.model_fields_set if hasattr(body, "model_fields_set") else body.__fields_set__
    if "assigned_to" in fields_set:
        a.assigned_to = body.assigned_to
    audit.log(db, actor, "attention_update", "attention_item", a.id, before, body.model_dump())
    db.commit()
    return to_dict(a)


@router.get("/dashboard/overview")
def overview(db=Depends(get_db), actor=Depends(get_actor)):
    require(actor, *STAFF)
    # "Today" = the UTC calendar day, same as services/checklist.py todays_items
    start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return {
        "active_patients": db.query(Patient).filter(Patient.journey_state != "DECEASED").count(),
        "consultations_today": db.query(CareEvent).filter(
            CareEvent.type == "APPOINTMENT", CareEvent.status != "RESCHEDULED",
            CareEvent.scheduled_at >= start, CareEvent.scheduled_at < end).count(),
        "missed_activities": db.query(CareEvent).filter(CareEvent.status.in_(["REPORTED_MISSED", "NO_RESPONSE"])).count(),
        "open_queries": db.query(PatientQuery).filter(PatientQuery.status != "RESOLVED").count(),
        "reports_pending_review": db.query(Report).filter_by(reviewed=False).count(),
        "sos_open": db.query(AttentionItem).filter_by(label="SOS").filter(AttentionItem.status != "CLOSED").count(),
    }
