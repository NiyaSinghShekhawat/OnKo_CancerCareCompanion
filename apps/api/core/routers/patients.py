import hashlib
import os
import re
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.db import get_db
from core.auth import STAFF, get_actor, require, require_patient_access
from core.models import Patient, CareEvent, CarePlanItem, PatientQuery, Report, Caregiver, AttentionItem, User, PatientAccess, PatientVerification
from core.serialize import to_dict
from core.services import attention, audit, journey_state, review
from core.timeutil import utcnow
from ai.summarize import since_last_review
from whatsapp import messages

router = APIRouter(tags=["patients"])


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


def _patient_id(name: str, db) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:18] or "patient"
    for _ in range(20):
        candidate = f"p_{slug}_{secrets.token_hex(2)}"
        if not db.get(Patient, candidate) and not db.get(User, candidate):
            return candidate
    raise HTTPException(500, "Unable to allocate patient id")


def _initial_password() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(8))


@router.get("/patients")
def list_patients(q: str | None = None, status: str | None = None, db=Depends(get_db), actor=Depends(get_actor)):
    require(actor, *STAFF)
    query = db.query(Patient)
    if q:
        query = query.filter(Patient.name.ilike(f"%{q}%"))
    if status:
        query = query.filter(Patient.journey_state == status)
    return [to_dict(p) for p in query.all()]


class EnrollmentOtpIn(BaseModel):
    phone: str


@router.post("/patients/enrollment/send-otp")
def send_enrollment_otp(body: EnrollmentOtpIn, db=Depends(get_db), actor=Depends(get_actor)):
    require(actor, "doctor")
    phone = _normalize_whatsapp(body.phone)
    otp = f"{secrets.randbelow(1_000_000):06d}"
    now = datetime.utcnow()
    verification = PatientVerification(
        phone_whatsapp=phone,
        otp_hash=_hash_secret(otp),
        expires_at=now + timedelta(minutes=10),
    )
    db.add(verification)
    db.commit()

    sent = messages.send(phone, messages.render_enrollment_otp(otp))
    response = {"sent": sent, "expires_in_minutes": 10, "phone": phone}
    if os.getenv("ONKO_DEMO_OTP_ECHO", "").lower() == "true":
        response["demo_otp"] = otp
    return response


class EnrollmentVerifyIn(BaseModel):
    phone: str
    otp: str


@router.post("/patients/enrollment/verify-otp")
def verify_enrollment_otp(body: EnrollmentVerifyIn, db=Depends(get_db), actor=Depends(get_actor)):
    require(actor, "doctor")
    phone = _normalize_whatsapp(body.phone)
    verification = (
        db.query(PatientVerification)
        .filter_by(phone_whatsapp=phone)
        .order_by(PatientVerification.created_at.desc())
        .first()
    )
    if not verification:
        raise HTTPException(404, "No verification code has been sent for this number")
    now = datetime.utcnow()
    if verification.expires_at < now:
        raise HTTPException(400, "Verification code expired. Send a new code.")
    if verification.attempts >= 5:
        raise HTTPException(429, "Too many verification attempts. Send a new code.")

    verification.attempts += 1
    if verification.otp_hash != _hash_secret(body.otp.strip()):
        db.commit()
        raise HTTPException(400, "Incorrect verification code")

    verification.verified_at = now
    db.commit()
    return {"verified": True, "phone": phone}


class EnrollPatientIn(BaseModel):
    name: str
    age: int
    gender: str
    preferred_language: str = "English"
    phone: str
    abha_id: str | None = None
    diagnosis_label: str
    regimen_label: str = ""
    cycle_current: int = 0
    cycle_total: int = 0


@router.post("/patients/enroll")
def enroll_patient(body: EnrollPatientIn, db=Depends(get_db), actor=Depends(get_actor)):
    require(actor, "doctor")
    phone = _normalize_whatsapp(body.phone)
    now = datetime.utcnow()

    verification = (
        db.query(PatientVerification)
        .filter_by(phone_whatsapp=phone)
        .order_by(PatientVerification.created_at.desc())
        .first()
    )
    if not verification or not verification.verified_at:
        raise HTTPException(400, "Verify the patient's WhatsApp number before enrollment")
    if verification.verified_at < now - timedelta(minutes=30):
        raise HTTPException(400, "Number verification is too old. Verify the number again.")
    if db.query(Patient).filter_by(phone_whatsapp=phone).first():
        raise HTTPException(409, "A patient with this WhatsApp number is already enrolled")
    if not db.get(User, actor.user_id):
        raise HTTPException(400, "Doctor account is not available in the current database")

    pid = _patient_id(body.name, db)
    diagnosis = body.diagnosis_label.strip()
    if diagnosis and "(as recorded)" not in diagnosis.lower():
        diagnosis += " (as recorded)"

    db.add(User(id=pid, name=body.name.strip(), role="patient"))
    db.flush()
    patient = Patient(
        id=pid,
        name=body.name.strip(),
        age=body.age,
        gender=body.gender,
        abha_id=(body.abha_id or "").strip() or None,
        phone_whatsapp=phone,
        preferred_language=body.preferred_language,
        diagnosis_label=diagnosis,
        regimen_label=body.regimen_label.strip(),
        cycle_current=max(0, body.cycle_current),
        cycle_total=max(0, body.cycle_total),
        doctor_id=actor.user_id,
    )
    db.add(patient)
    db.flush()

    password = _initial_password()
    db.add(PatientAccess(
        patient_id=pid,
        access_code_hash=_hash_secret(password),
        active=True,
        must_change=True,
    ))
    audit.log(
        db, actor, "patient_enrolled", "patient", pid, None,
        {"phone_whatsapp": phone, "preferred_language": body.preferred_language},
    )
    db.commit()

    login_url = os.getenv("PATIENT_LOGIN_URL", "http://localhost:3000/patient/login")
    sent = messages.send(
        phone,
        messages.render_patient_access(body.name.strip(), pid, password, login_url),
    )
    response = {
        "patient": to_dict(patient),
        "login_id": pid,
        "whatsapp_sent": sent,
    }
    if not sent:
        response["warning"] = "Patient created, but WhatsApp delivery is not configured or failed."
    if os.getenv("ONKO_DEMO_CREDENTIAL_ECHO", "").lower() == "true":
        response["demo_password"] = password
    return response


class PatientLoginIn(BaseModel):
    patient_id: str
    password: str | None = None
    access_code: str | None = None  # backward compatibility for older clients


@router.post("/patient-auth/login")
def patient_login(body: PatientLoginIn, db=Depends(get_db)):
    patient_id = body.patient_id.strip()
    access = db.get(PatientAccess, patient_id)
    patient = db.get(Patient, patient_id)
    if not patient or not access or not access.active:
        raise HTTPException(401, "Invalid patient ID or password")
    supplied = (body.password or body.access_code or "").strip().upper()
    if not supplied or access.access_code_hash != _hash_secret(supplied):
        raise HTTPException(401, "Invalid patient ID or password")
    access.last_login_at = datetime.utcnow()
    db.commit()
    return {
        "ok": True,
        "patient_id": patient.id,
        "name": patient.name,
        "must_change": access.must_change,
    }


@router.get("/patients/{pid}")
def get_patient(pid: str, db=Depends(get_db), actor=Depends(get_actor)):
    require_patient_access(actor, pid, db, allow_caregivers=False)   # caregivers: /caregivers/{id}/view
    p = db.get(Patient, pid)
    if not p:
        raise HTTPException(404, "Patient not found")
    return to_dict(p)


@router.get("/patients/{pid}/timeline")
def timeline(pid: str, db=Depends(get_db), actor=Depends(get_actor)):
    require_patient_access(actor, pid, db, allow_caregivers=False)
    events = db.query(CareEvent).filter_by(patient_id=pid).order_by(CareEvent.scheduled_at).all()
    return [to_dict(e) for e in events]


@router.get("/patients/{pid}/360")
def patient_360(pid: str, db=Depends(get_db), actor=Depends(get_actor)):
    # Caregivers use their own minimized /caregivers/{id}/view instead.
    require_patient_access(actor, pid, db, allow_caregivers=False)
    p = db.get(Patient, pid)
    if not p:
        raise HTTPException(404, "Patient not found")
    events = db.query(CareEvent).filter_by(patient_id=pid).order_by(CareEvent.scheduled_at).all()
    queries = db.query(PatientQuery).filter_by(patient_id=pid).order_by(PatientQuery.created_at).all()
    reports = db.query(Report).filter_by(patient_id=pid).order_by(Report.uploaded_at).all()
    attention_items = db.query(AttentionItem).filter_by(patient_id=pid).order_by(AttentionItem.created_at.desc()).all()

    since, now = p.last_reviewed_at, utcnow()
    new_events = [e for e in events if not since or e.scheduled_at >= since or review.is_open_today(e, now)]
    new_queries = [q for q in queries if not since or q.created_at >= since]
    new_reports = [r for r in reports if not since or r.uploaded_at >= since]
    try:
        summary = since_last_review([to_dict(e) for e in new_events], [to_dict(q) for q in new_queries],
                                    [to_dict(r) for r in new_reports])
    except Exception:
        summary = None
    if not summary or not summary.get("ok"):
        summary = review.fallback_summary(new_events, new_queries, new_reports, since, now)

    return {
        "patient": to_dict(p),
        "care_plan": [to_dict(x) for x in db.query(CarePlanItem).filter_by(patient_id=pid)],
        "timeline": [to_dict(x) for x in events],
        "open_queries": [to_dict(x) for x in queries if x.status != "RESOLVED"],
        "query_history": [to_dict(x) for x in reversed(queries)],
        "reports": [to_dict(x) for x in reports],
        "caregivers": [to_dict(x) for x in db.query(Caregiver).filter_by(patient_id=pid)],
        # Attention is an internal care-team workflow; do not expose these operational flags to patients.
        "attention": [to_dict(x) for x in attention_items if x.status in {"PENDING", "ACKNOWLEDGED"}] if actor.role in STAFF else [],
        "attention_history": [to_dict(x) for x in attention_items] if actor.role in STAFF else [],
        "since_last_review": summary,
    }


@router.post("/patients/{pid}/mark-reviewed")
def mark_reviewed(pid: str, db=Depends(get_db), actor=Depends(get_actor)):
    require(actor, "doctor")
    p = db.get(Patient, pid)
    if not p:
        raise HTTPException(404, "Patient not found")
    before = p.last_reviewed_at.isoformat() if p.last_reviewed_at else None
    p.last_reviewed_at = utcnow()
    audit.log(db, actor, "patient_marked_reviewed", "patient", pid,
              {"last_reviewed_at": before}, {"last_reviewed_at": p.last_reviewed_at.isoformat()})
    db.commit()
    return to_dict(p)


class JourneyStateIn(BaseModel):
    state: str
    reason: str = ""


@router.patch("/patients/{pid}/journey-state")
def set_journey_state(pid: str, body: JourneyStateIn, db=Depends(get_db), actor=Depends(get_actor)):
    require(actor, "doctor")
    p = db.get(Patient, pid)
    if not p:
        raise HTTPException(404, "Patient not found")
    before = p.journey_state
    if body.state != before:
        p.journey_state_changed_at = utcnow()
        p.previous_journey_state = before
    p.journey_state = body.state
    audit.log(db, actor, "journey_state_change", "patient", pid, {"state": before}, {"state": body.state, "reason": body.reason})
    if body.state != before and journey_state.starts_new_chapter(body.state):
        # History is kept: earlier events stay in their chapter; only new events get the new number.
        p.journey_chapter = (p.journey_chapter or 1) + 1
        audit.log(db, actor, "journey_chapter_started", "patient", pid,
                  {"journey_chapter": p.journey_chapter - 1}, {"journey_chapter": p.journey_chapter, "state": body.state})
    attention.apply_journey_state(db, p, actor)
    db.commit()
    return to_dict(p)
