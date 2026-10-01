from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.db import get_db
from core.auth import get_actor, require, require_patient_access
from core.models import Caregiver, CareEvent, Patient
from core.serialize import to_dict
from core.services import audit, journey_state, review

router = APIRouter(tags=["caregivers"])


class CaregiverIn(BaseModel):
    name: str
    relation: str
    phone_whatsapp: str
    type: str = "family"


@router.get("/patients/{pid}/caregivers")
def list_cg(pid: str, db=Depends(get_db), actor=Depends(get_actor)):
    require_patient_access(actor, pid, db)
    return [to_dict(c) for c in db.query(Caregiver).filter_by(patient_id=pid)]


@router.post("/patients/{pid}/caregivers")
def invite(pid: str, body: CaregiverIn, db=Depends(get_db), actor=Depends(get_actor)):
    require_patient_access(actor, pid, db, allow_caregivers=False)   # caregivers can't add caregivers
    cg = Caregiver(patient_id=pid, **body.model_dump(), consent_status="PENDING")
    db.add(cg)
    db.flush()
    audit.log(db, actor, "caregiver_invited", "caregiver", cg.id, None, body.model_dump())
    db.commit()
    return to_dict(cg)


class CaregiverUpdate(BaseModel):
    consent_status: str | None = None
    permissions: dict | None = None


@router.patch("/caregivers/{cid}")
def update_cg(cid: str, body: CaregiverUpdate, db=Depends(get_db), actor=Depends(get_actor)):
    cg = db.get(Caregiver, cid)
    if not cg:
        raise HTTPException(404, "Not found")
    require_patient_access(actor, cg.patient_id, db, allow_caregivers=False)   # no granting yourself permissions
    before = {"consent_status": cg.consent_status, "permissions": cg.permissions}
    if body.consent_status:
        cg.consent_status = body.consent_status
    if body.permissions is not None:
        cg.permissions = body.permissions
    audit.log(db, actor, "caregiver_updated", "caregiver", cg.id, before, body.model_dump())
    db.commit()
    return to_dict(cg)


VIEW_DAYS = 7
RECENT_STATUSES = {"COMPLETED", "REPORTED_MISSED", "NO_RESPONSE"}


def _event_summary(e: CareEvent) -> dict:
    """Data minimization: no details (doses, instructions), nothing beyond what's needed to follow along."""
    return {"id": e.id, "type": e.type, "title": e.title, "scheduled_at": e.scheduled_at.isoformat(), "status": e.status}


@router.get("/caregivers/{cid}/view")
def caregiver_view(cid: str, db=Depends(get_db), actor=Depends(get_actor)):
    """What a consented caregiver may see. No diagnosis, reports, queries, attention items or event details."""
    require(actor, "caregiver", "doctor")
    if actor.role == "caregiver" and actor.user_id != cid:
        raise HTTPException(403, "Caregivers can only open their own view")
    cg = db.get(Caregiver, cid)
    if not cg:
        raise HTTPException(404, "Caregiver not found")
    perms = cg.permissions or {}
    if cg.consent_status != "GRANTED" or not perms.get("view_journey"):
        raise HTTPException(403, "Caregiver access not granted")

    p = db.get(Patient, cg.patient_id)
    now = datetime.utcnow()
    window = timedelta(days=VIEW_DAYS)
    events = (db.query(CareEvent)
              .filter(CareEvent.patient_id == p.id,
                      CareEvent.scheduled_at >= now - window, CareEvent.scheduled_at < now + window)
              .order_by(CareEvent.scheduled_at).all())
    upcoming = [e for e in events if e.scheduled_at >= now or review.is_open_today(e, now)]
    if not journey_state.caregiver_sees_upcoming(p.journey_state):
        upcoming = []
    recent = [e for e in reversed(events) if e.scheduled_at < now and e.status in RECENT_STATUSES]

    audit.log(db, actor, "caregiver_view_accessed", "caregiver", cg.id, None, {"patient_id": p.id})
    db.commit()
    return {
        "patient": {"id": p.id, "name": p.name, "journey_state": p.journey_state,
                    "preferred_language": p.preferred_language},
        "upcoming": [_event_summary(e) for e in upcoming],
        "recent": [_event_summary(e) for e in recent],
        "can_upload_reports": bool(perms.get("upload_reports")),
        "receives_escalations": bool(perms.get("receive_escalations")),
    }
