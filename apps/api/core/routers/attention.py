from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.db import get_db
from core.auth import STAFF, get_actor, require
from core.models import AttentionItem, Patient, PatientQuery, Report, CareEvent, User
from core.serialize import to_dict
from core.services import audit
from core.timeutil import utcnow


router = APIRouter(tags=["attention"])
ORDER = {"SOS": 0, "NEEDS_REVIEW": 1, "QUERY": 2, "FOLLOW_UP": 3}


LABELS = set(ORDER)
STATUSES = {"PENDING", "ACKNOWLEDGED", "HANDLED", "CLOSED"}


def _queue(query) -> list[dict]:
    items = query.all()
    items.sort(key=lambda i: (ORDER.get(i.label, 9), i.created_at))
    return [to_dict(i) for i in items]


@router.get("/attention")
def list_attention(assigned_to: str | None = None, label: str | None = None, patient_id: str | None = None,
                   status: str | None = None, db=Depends(get_db), actor=Depends(get_actor)):
    """Filters combine. Without ?status=, CLOSED items are left out; ?status=CLOSED shows them."""
    require(actor, *STAFF)
    if label is not None and label not in LABELS:
        raise HTTPException(400, f"Unknown label; use one of {sorted(LABELS)}")
    if status is not None and status not in STATUSES:
        raise HTTPException(400, f"Unknown status; use one of {sorted(STATUSES)}")
    q = db.query(AttentionItem)
    q = (
        q.filter(AttentionItem.status == status)
        if status
        else q.filter(AttentionItem.status.in_(["PENDING", "ACKNOWLEDGED"]))
    )
    if assigned_to is not None:
        q = q.filter(AttentionItem.assigned_to == assigned_to)
    if label is not None:
        q = q.filter(AttentionItem.label == label)
    if patient_id is not None:
        q = q.filter(AttentionItem.patient_id == patient_id)
    return _queue(q)


@router.get("/attention/mine")
def my_attention(db=Depends(get_db), actor=Depends(get_actor)):
    """Open items assigned to the caller (CLOSED left out, like the main queue)."""
    require(actor, *STAFF)
    return _queue(db.query(AttentionItem).filter(
        AttentionItem.assigned_to == actor.user_id,
        AttentionItem.status.in_(["PENDING", "ACKNOWLEDGED"])
    ))


class AttentionUpdate(BaseModel):
    status: str | None = None        # omit to only assign / hand off
    assigned_to: str | None = None   # a doctor or care_team user id


@router.patch("/attention/{aid}")
def update_attention(aid: str, body: AttentionUpdate, db=Depends(get_db), actor=Depends(get_actor)):
    require(actor, *STAFF)
    a = db.get(AttentionItem, aid)
    if not a:
        raise HTTPException(404, "Not found")
    if actor.role == "care_team" and a.assigned_to not in (None, actor.user_id):
        # Checked against the current assignee, so a nurse can't take someone else's item and then close it.
        raise HTTPException(403, "This item is assigned to someone else")
    if body.assigned_to is not None:
        assignee = db.get(User, body.assigned_to)
        if not assignee or assignee.role not in STAFF:
            raise HTTPException(400, "assigned_to must be a doctor or care_team user id")

    if body.status is not None and body.status != a.status:
        before = a.status
        a.status = body.status
        audit.log(db, actor, "attention_update", "attention_item", a.id, {"status": before}, {"status": a.status})
    if body.assigned_to is not None and body.assigned_to != a.assigned_to:
        before = a.assigned_to
        a.assigned_to = body.assigned_to
        audit.log(db, actor, "attention_handoff" if before else "attention_assigned", "attention_item", a.id,
                  {"assigned_to": before}, {"assigned_to": a.assigned_to})
    db.commit()
    return to_dict(a)


@router.get("/dashboard/overview")
def overview(db=Depends(get_db), actor=Depends(get_actor)):
    require(actor, *STAFF)
    # "Today" = the UTC calendar day, same as services/checklist.py todays_items
    start = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return {
        "active_patients": db.query(Patient).filter(Patient.journey_state != "DECEASED").count(),
        "consultations_today": db.query(CareEvent).filter(
            CareEvent.type == "APPOINTMENT", CareEvent.status != "RESCHEDULED",
            CareEvent.scheduled_at >= start, CareEvent.scheduled_at < end).count(),
        "missed_activities": db.query(CareEvent).filter(CareEvent.status.in_(["REPORTED_MISSED", "NO_RESPONSE"])).count(),
        "open_queries": db.query(PatientQuery).filter(PatientQuery.status != "RESOLVED").count(),
        "reports_pending_review": db.query(Report).filter_by(reviewed=False).count(),
        "sos_open": db.query(AttentionItem)
            .filter_by(label="SOS")
            .filter(AttentionItem.status.in_(["PENDING", "ACKNOWLEDGED"]))
            .count(),
    }
