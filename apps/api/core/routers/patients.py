from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.db import get_db
from core.auth import get_actor, require
from core.models import Patient, CareEvent, CarePlanItem, PatientQuery, Report, Caregiver, AttentionItem
from core.serialize import to_dict
from core.services import audit, review
from ai.summarize import since_last_review

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
    events = db.query(CareEvent).filter_by(patient_id=pid).order_by(CareEvent.scheduled_at).all()
    queries = db.query(PatientQuery).filter_by(patient_id=pid).order_by(PatientQuery.created_at).all()
    reports = db.query(Report).filter_by(patient_id=pid).order_by(Report.uploaded_at).all()

    since, now = p.last_reviewed_at, datetime.utcnow()
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
        "reports": [to_dict(x) for x in reports],
        "caregivers": [to_dict(x) for x in db.query(Caregiver).filter_by(patient_id=pid)],
        "attention": [to_dict(x) for x in db.query(AttentionItem).filter_by(patient_id=pid)],
        "since_last_review": summary,
    }


@router.post("/patients/{pid}/mark-reviewed")
def mark_reviewed(pid: str, db=Depends(get_db), actor=Depends(get_actor)):
    require(actor, "doctor")
    p = db.get(Patient, pid)
    if not p:
        raise HTTPException(404, "Patient not found")
    before = p.last_reviewed_at.isoformat() if p.last_reviewed_at else None
    p.last_reviewed_at = datetime.utcnow()
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
    p.journey_state = body.state
    audit.log(db, actor, "journey_state_change", "patient", pid, {"state": before}, {"state": body.state, "reason": body.reason})
    db.commit()
    return to_dict(p)
