from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.db import get_db
from core.auth import get_actor
from core.models import Report, Patient, Caregiver
from core.serialize import to_dict
from core.services import audit, attention
from ai.extract import extract_report_values

router = APIRouter(tags=["reports"])


class ReportIn(BaseModel):
    title: str
    text: str
    uploaded_by_role: str = "patient"


@router.post("/patients/{pid}/reports")
def upload(pid: str, body: ReportIn, db=Depends(get_db), actor=Depends(get_actor)):
    p = db.get(Patient, pid)
    if not p:
        raise HTTPException(404, "Patient not found")
    if actor.role == "caregiver":
        cg = db.query(Caregiver).filter_by(id=actor.user_id, patient_id=pid, consent_status="GRANTED").first()
        if not cg or not cg.permissions.get("upload_reports"):
            raise HTTPException(403, "Caregiver has no upload permission")
    ext = extract_report_values(body.text)
    r = Report(patient_id=pid, title=body.title, text=body.text,
               extracted_values=ext.get("values", []), uploaded_by_role=body.uploaded_by_role)
    db.add(r)
    db.flush()
    attention.raise_item(db, p, "NEEDS_REVIEW", f"New report awaiting review: {body.title}")
    audit.log(db, actor, "report_uploaded", "report", r.id, None, {"title": body.title})
    db.commit()
    return to_dict(r)


@router.get("/patients/{pid}/reports")
def list_reports(pid: str, db=Depends(get_db)):
    return [to_dict(r) for r in db.query(Report).filter_by(patient_id=pid)]
