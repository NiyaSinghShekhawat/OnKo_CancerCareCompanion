from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.db import get_db
from core.auth import get_actor, require
from core.models import Caregiver, CareEvent, Patient
from core.serialize import to_dict
from core.services import audit

router = APIRouter(tags=["caregivers"])


class CaregiverIn(BaseModel):
    name: str
    relation: str
    phone_whatsapp: str
    type: str = "family"


@router.get("/patients/{pid}/caregivers")
def list_cg(pid: str, db=Depends(get_db)):
    return [to_dict(c) for c in db.query(Caregiver).filter_by(patient_id=pid)]


@router.post("/patients/{pid}/caregivers")
def invite(pid: str, body: CaregiverIn, db=Depends(get_db), actor=Depends(get_actor)):
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


def _minimized_event(event):
    return {
        "id": event.id,
        "type": event.type,
        "title": event.title,
        "scheduled_at": event.scheduled_at.isoformat(),
        "status": event.status,
    }


@router.get("/caregivers/{cid}/view")
def caregiver_view(cid: str, db=Depends(get_db), actor=Depends(get_actor)):
    """Consent-limited caregiver dashboard view.

    Returns only basic patient identity/journey state plus minimized care events.
    No diagnosis, report values, queries, attention items, or clinical interpretation.
    """
    require(actor, "caregiver", "doctor")
    if actor.role == "caregiver" and actor.user_id != cid:
        raise HTTPException(403, "Caregivers can only open their own view")

    cg = db.get(Caregiver, cid)
    if not cg:
        raise HTTPException(404, "Caregiver not found")

    permissions = cg.permissions or {}
    if cg.consent_status != "GRANTED" or not permissions.get("view_journey", False):
        raise HTTPException(403, "Caregiver access not granted")

    patient = db.get(Patient, cg.patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")

    now = datetime.utcnow()
    window = timedelta(days=VIEW_DAYS)
    events = (
        db.query(CareEvent)
        .filter(
            CareEvent.patient_id == patient.id,
            CareEvent.scheduled_at >= now - window,
            CareEvent.scheduled_at < now + window,
        )
        .order_by(CareEvent.scheduled_at)
        .all()
    )

    upcoming = [e for e in events if e.scheduled_at >= now]
    if patient.journey_state == "DECEASED":
        upcoming = []

    recent = [
        e for e in reversed(events)
        if e.scheduled_at < now and e.status in RECENT_STATUSES
    ]

    audit.log(
        db,
        actor,
        "caregiver_view_accessed",
        "caregiver",
        cg.id,
        None,
        {"patient_id": patient.id},
    )
    db.commit()

    return {
        "patient": {
            "id": patient.id,
            "name": patient.name,
            "journey_state": patient.journey_state,
            "preferred_language": patient.preferred_language,
        },
        "upcoming": [_minimized_event(e) for e in upcoming],
        "recent": [_minimized_event(e) for e in recent],
        "can_upload_reports": bool(permissions.get("upload_reports")),
        "receives_escalations": bool(permissions.get("receive_escalations")),
    }
