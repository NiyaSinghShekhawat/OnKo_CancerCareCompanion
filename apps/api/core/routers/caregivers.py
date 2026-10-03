import hashlib
import os
import re
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.auth import get_actor, require
from core.db import get_db
from core.models import Caregiver, CaregiverAccess, CareEvent, Patient
from core.serialize import to_dict
from core.services import audit
from whatsapp import messages

router = APIRouter(tags=["caregivers"])


def _hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize_whatsapp(raw: str) -> str:
    value = raw.strip()
    if value.startswith("whatsapp:"):
        value = value[len("whatsapp:"):]
    digits = re.sub(r"\D", "", value)
    if len(digits) == 10:
        digits = "91" + digits
    if not 10 <= len(digits) <= 15:
        raise HTTPException(400, "Enter a valid mobile number with country code")
    return "whatsapp:+" + digits


def _caregiver_id(name: str, db) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:18] or "caregiver"
    for _ in range(20):
        candidate = f"cg_{slug}_{secrets.token_hex(2)}"
        if not db.get(Caregiver, candidate):
            return candidate
    raise HTTPException(500, "Unable to allocate caregiver id")


def _initial_password() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(8))


def _can_manage(actor, patient_id: str) -> bool:
    return actor.role == "doctor" or (actor.role == "patient" and actor.user_id == patient_id)


class CaregiverIn(BaseModel):
    name: str
    relation: str
    phone_whatsapp: str
    type: str = "family"


@router.get("/patients/{pid}/caregivers")
def list_cg(pid: str, db=Depends(get_db), actor=Depends(get_actor)):
    if not _can_manage(actor, pid):
        raise HTTPException(403, "Only the patient or care team can manage caregiver access")
    return [to_dict(c) for c in db.query(Caregiver).filter_by(patient_id=pid).all()]


@router.post("/patients/{pid}/caregivers")
def invite(pid: str, body: CaregiverIn, db=Depends(get_db), actor=Depends(get_actor)):
    if not _can_manage(actor, pid):
        raise HTTPException(403, "Only the patient or care team can add a caregiver")
    patient = db.get(Patient, pid)
    if not patient:
        raise HTTPException(404, "Patient not found")

    phone = _normalize_whatsapp(body.phone_whatsapp)
    existing = db.query(Caregiver).filter_by(patient_id=pid, phone_whatsapp=phone).first()
    if existing and existing.consent_status != "REVOKED":
        raise HTTPException(409, "This caregiver is already linked to the patient")

    password = _initial_password()
    if existing:
        cg = existing
        cg.name = body.name.strip()
        cg.relation = body.relation.strip()
        cg.type = body.type
        cg.consent_status = "GRANTED"
        cg.permissions = cg.permissions or {
            "view_journey": True,
            "upload_reports": False,
            "receive_escalations": True,
        }
        access = db.get(CaregiverAccess, cg.id)
        if access:
            access.password_hash = _hash_secret(password)
            access.active = True
        else:
            db.add(CaregiverAccess(caregiver_id=cg.id, password_hash=_hash_secret(password), active=True))
    else:
        cid = _caregiver_id(body.name, db)
        cg = Caregiver(
            id=cid,
            patient_id=pid,
            name=body.name.strip(),
            relation=body.relation.strip(),
            phone_whatsapp=phone,
            type=body.type,
            consent_status="GRANTED",
            permissions={
                "view_journey": True,
                "upload_reports": False,
                "receive_escalations": True,
            },
        )
        db.add(cg)
        db.flush()
        db.add(CaregiverAccess(caregiver_id=cg.id, password_hash=_hash_secret(password), active=True))

    audit.log(
        db, actor, "caregiver_access_granted", "caregiver", cg.id, None,
        {"patient_id": pid, "relation": cg.relation},
    )
    db.commit()

    login_url = os.getenv("CAREGIVER_LOGIN_URL", "http://localhost:3000/caregiver/login")
    sent = messages.send(
        phone,
        messages.render_caregiver_access(cg.name, patient.name, cg.id, password, login_url),
    )
    response = {
        "caregiver": to_dict(cg),
        "login_id": cg.id,
        "whatsapp_sent": sent,
        # Returned once to the authenticated patient who created access.
        # Only the hash is persisted in the database.
        "password": password,
    }
    if not sent:
        response["warning"] = "Caregiver added, but WhatsApp credential delivery failed or is not configured."
    if os.getenv("ONKO_DEMO_CREDENTIAL_ECHO", "").lower() == "true":
        response["demo_password"] = password
    return response


class CaregiverUpdate(BaseModel):
    permissions: dict | None = None


@router.patch("/caregivers/{cid}")
def update_cg(cid: str, body: CaregiverUpdate, db=Depends(get_db), actor=Depends(get_actor)):
    cg = db.get(Caregiver, cid)
    if not cg:
        raise HTTPException(404, "Caregiver not found")
    if not _can_manage(actor, cg.patient_id):
        raise HTTPException(403, "Only the patient or care team can change caregiver permissions")
    before = {"permissions": cg.permissions}
    if body.permissions is not None:
        cg.permissions = body.permissions
    audit.log(db, actor, "caregiver_permissions_updated", "caregiver", cg.id, before, {"permissions": cg.permissions})
    db.commit()
    return to_dict(cg)


@router.post("/caregivers/{cid}/revoke")
def revoke_caregiver(cid: str, db=Depends(get_db), actor=Depends(get_actor)):
    cg = db.get(Caregiver, cid)
    if not cg:
        raise HTTPException(404, "Caregiver not found")
    if not _can_manage(actor, cg.patient_id):
        raise HTTPException(403, "Only the patient or care team can revoke caregiver access")
    cg.consent_status = "REVOKED"
    access = db.get(CaregiverAccess, cid)
    if access:
        access.active = False
    audit.log(db, actor, "caregiver_access_revoked", "caregiver", cid, None, {"patient_id": cg.patient_id})
    db.commit()
    return to_dict(cg)


@router.post("/caregivers/{cid}/reinvite")
def reinvite_caregiver(cid: str, db=Depends(get_db), actor=Depends(get_actor)):
    cg = db.get(Caregiver, cid)
    if not cg:
        raise HTTPException(404, "Caregiver not found")
    if not _can_manage(actor, cg.patient_id):
        raise HTTPException(403, "Only the patient or care team can restore caregiver access")
    cg.consent_status = "GRANTED"
    access = db.get(CaregiverAccess, cid)
    if access:
        access.active = True
    audit.log(db, actor, "caregiver_access_restored", "caregiver", cid, None, {"patient_id": cg.patient_id})
    db.commit()
    return to_dict(cg)


class CaregiverLoginIn(BaseModel):
    caregiver_id: str
    password: str


@router.post("/caregiver-auth/login")
def caregiver_login(body: CaregiverLoginIn, db=Depends(get_db)):
    cid = body.caregiver_id.strip()
    cg = db.get(Caregiver, cid)
    access = db.get(CaregiverAccess, cid)
    if not cg or not access or not access.active or cg.consent_status != "GRANTED":
        raise HTTPException(401, "Invalid caregiver ID or password")
    supplied = body.password.strip().upper()
    if not supplied or access.password_hash != _hash_secret(supplied):
        raise HTTPException(401, "Invalid caregiver ID or password")
    access.last_login_at = datetime.utcnow()
    db.commit()
    return {
        "ok": True,
        "caregiver_id": cg.id,
        "name": cg.name,
        "patient_id": cg.patient_id,
    }


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
    recent = [e for e in reversed(events) if e.scheduled_at < now and e.status in RECENT_STATUSES]

    audit.log(db, actor, "caregiver_view_accessed", "caregiver", cg.id, None, {"patient_id": patient.id})
    db.commit()

    return {
        "caregiver": to_dict(cg),
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
