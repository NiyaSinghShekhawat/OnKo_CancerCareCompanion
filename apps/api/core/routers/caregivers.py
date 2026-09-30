from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.db import get_db
from core.auth import get_actor
from core.models import Caregiver
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
