from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.db import get_db
from core.auth import get_actor, require
from core.models import Patient, CareEvent, CarePlanItem, PatientQuery, Report, Caregiver, AttentionItem
from core.serialize import to_dict
from core.services import audit

router = APIRouter(tags=["patients"])


@router.get("/patients")
def list_patients(q: str | None = None, status: str | None = None, db=Depends(get_db)):
    query = db.query(Patient)
    if q:
        query = query.filter(Patient.name.ilike(f"%{q}%"))
    if status:
        query = query.filter(Patient.journey_state == status)
    return [to_dict(p) for p in query.all()]


@router.get("/patients/{pid}")
def get_patient(pid: str, db=Depends(get_db)):
    p = db.get(Patient, pid)
    if not p:
        raise HTTPException(404, "Patient not found")
    return to_dict(p)


@router.get("/patients/{pid}/timeline")
def timeline(pid: str, db=Depends(get_db)):
    events = db.query(CareEvent).filter_by(patient_id=pid).order_by(CareEvent.scheduled_at).all()
    return [to_dict(e) for e in events]


@router.get("/patients/{pid}/360")
def patient_360(pid: str, db=Depends(get_db)):
    p = db.get(Patient, pid)
    if not p:
        raise HTTPException(404, "Patient not found")
    # TODO(Samprada): call ai.summarize.since_last_review with events since p.last_reviewed_at
    return {
        "patient": to_dict(p),
        "care_plan": [to_dict(x) for x in db.query(CarePlanItem).filter_by(patient_id=pid)],
        "timeline": [to_dict(x) for x in db.query(CareEvent).filter_by(patient_id=pid).order_by(CareEvent.scheduled_at)],
        "open_queries": [to_dict(x) for x in db.query(PatientQuery).filter_by(patient_id=pid).filter(PatientQuery.status != "RESOLVED")],
        "reports": [to_dict(x) for x in db.query(Report).filter_by(patient_id=pid)],
        "caregivers": [to_dict(x) for x in db.query(Caregiver).filter_by(patient_id=pid)],
        "attention": [to_dict(x) for x in db.query(AttentionItem).filter_by(patient_id=pid)],
        "since_last_review": {"ok": False, "since": None, "bullets": [], "upcoming": []},
    }


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
    p.journey_state = body.state
    audit.log(db, actor, "journey_state_change", "patient", pid, {"state": before}, {"state": body.state, "reason": body.reason})
    db.commit()
    return to_dict(p)
