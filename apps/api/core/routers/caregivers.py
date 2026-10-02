from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.db import get_db
from core.auth import get_actor, require, require_patient_access
from core.models import Caregiver, CareEvent, Patient
from core.serialize import minimized_event, to_dict
from core.services import audit, journey_state, review
from core.timeutil import utcnow

router = APIRouter(tags=["caregivers"])


class CaregiverIn(BaseModel):
    name: str
    relation: str
    phone_whatsapp: str
    type: str = "family"


@router.get("/patients/{pid}/caregivers")
def list_cg(pid: str, db=Depends(get_db), actor=Depends(get_actor)):
    require_patient_access(actor, pid, db, allow_caregivers=False)   # other caregivers' numbers stay private
    return [to_dict(c) for c in db.query(Caregiver).filter_by(patient_id=pid)]


@router.post("/patients/{pid}/caregivers")
def invite(pid: str, body: CaregiverIn, db=Depends(get_db), actor=Depends(get_actor)):
    require_patient_access(actor, pid, db, allow_caregivers=False)   # caregivers can't add caregivers
    if not db.get(Patient, pid):
        raise HTTPException(404, "Patient not found")   # caregivers.patient_id is a foreign key (enforced on Postgres)
    cg = Caregiver(patient_id=pid, **body.model_dump(), consent_status="PENDING")
    db.add(cg)
    db.flush()
    audit.log(db, actor, "caregiver_invited", "caregiver", cg.id, None, body.model_dump())
    db.commit()
    return to_dict(cg)


class CaregiverUpdate(BaseModel):
    consent_status: str | None = None   # rejected: consent moves only through accept / revoke / reinvite
    permissions: dict | None = None


def _get_cg(db, cid: str) -> Caregiver:
    cg = db.get(Caregiver, cid)
    if not cg:
        raise HTTPException(404, "Caregiver not found")
    return cg


@router.patch("/caregivers/{cid}")
def update_cg(cid: str, body: CaregiverUpdate, db=Depends(get_db), actor=Depends(get_actor)):
    """Assign responsibilities (permissions). Consent has its own routes."""
    if body.consent_status is not None:
        raise HTTPException(400, "consent_status can't be set here. Use POST /caregivers/{id}/accept, "
                                 "/caregivers/{id}/revoke or /caregivers/{id}/reinvite")
    cg = _get_cg(db, cid)
    require_patient_access(actor, cg.patient_id, db, allow_caregivers=False)   # no granting yourself permissions
    before = {"permissions": cg.permissions}
    if body.permissions is not None:
        cg.permissions = body.permissions
    audit.log(db, actor, "caregiver_updated", "caregiver", cg.id, before, {"permissions": cg.permissions})
    db.commit()
    return to_dict(cg)


# ---- Consent lifecycle: Invite (POST /patients/{id}/caregivers) → Accept → Switch / Revoke → Re-invite ----

def _move_consent(db, actor, cg: Caregiver, to: str, action: str) -> dict:
    before = cg.consent_status
    cg.consent_status = to
    audit.log(db, actor, action, "caregiver", cg.id, {"consent_status": before}, {"consent_status": to})
    db.commit()
    return to_dict(cg)


@router.post("/caregivers/{cid}/accept")
def accept_consent(cid: str, db=Depends(get_db), actor=Depends(get_actor)):
    """Only the invited caregiver can accept. PENDING → GRANTED."""
    require(actor, "caregiver")
    if actor.user_id != cid:
        raise HTTPException(403, "Only the invited caregiver can accept")
    cg = _get_cg(db, cid)
    if cg.consent_status == "GRANTED":
        return to_dict(cg)
    if cg.consent_status == "REVOKED":
        raise HTTPException(409, "Consent was revoked; the patient must re-invite")
    return _move_consent(db, actor, cg, "GRANTED", "caregiver_consent_accepted")


@router.post("/caregivers/{cid}/revoke")
def revoke_consent(cid: str, db=Depends(get_db), actor=Depends(get_actor)):
    """The patient (own caregivers), doctor / care_team, or the caregiver themself (stepping away).
    Any state → REVOKED; takes effect immediately, since every caregiver check and notify_caregivers look for
    GRANTED at the time of the call. No attention reasons or stored notifications are tied to a caregiver,
    so there is nothing else to clean up."""
    cg = _get_cg(db, cid)
    if not (actor.role == "caregiver" and actor.user_id == cid):
        require_patient_access(actor, cg.patient_id, db, allow_caregivers=False)
    if cg.consent_status == "REVOKED":
        return to_dict(cg)
    return _move_consent(db, actor, cg, "REVOKED", "caregiver_consent_revoked")


@router.post("/caregivers/{cid}/reinvite")
def reinvite(cid: str, db=Depends(get_db), actor=Depends(get_actor)):
    """The patient (own caregivers) or doctor / care_team. REVOKED → PENDING; the caregiver must accept again."""
    cg = _get_cg(db, cid)
    require_patient_access(actor, cg.patient_id, db, allow_caregivers=False)
    if cg.consent_status == "PENDING":
        return to_dict(cg)
    if cg.consent_status == "GRANTED":
        raise HTTPException(409, "Caregiver already has consent; nothing to re-invite")
    return _move_consent(db, actor, cg, "PENDING", "caregiver_reinvited")


VIEW_DAYS = 7
RECENT_STATUSES = {"COMPLETED", "REPORTED_MISSED", "NO_RESPONSE"}


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
    now = utcnow()
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
        "upcoming": [minimized_event(e) for e in upcoming],
        "recent": [minimized_event(e) for e in recent],
        "can_upload_reports": bool(perms.get("upload_reports")),
        "receives_escalations": bool(perms.get("receive_escalations")),
    }
