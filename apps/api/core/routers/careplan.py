"""Care Plan Copilot routes. AI output is only ever a DRAFT until the doctor approves."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.db import get_db
from core.auth import get_actor, require
from core.models import Patient, CarePlanDraft, CarePlanItem, CareEvent
from core.serialize import to_dict
from core.services import audit
from ai.copilot import structure_care_plan

router = APIRouter(tags=["careplan"])


class DraftIn(BaseModel):
    patient_id: str
    raw_text: str


@router.post("/careplan/draft")
def create_draft(body: DraftIn, db=Depends(get_db), actor=Depends(get_actor)):
    require(actor, "doctor")
    p = db.get(Patient, body.patient_id)
    if not p:
        raise HTTPException(404, "Patient not found")
    out = structure_care_plan(body.raw_text, to_dict(p))
    draft = CarePlanDraft(patient_id=p.id, raw_text=body.raw_text, items=out.get("items", []), created_by=actor.user_id)
    db.add(draft)
    db.flush()
    audit.log(db, actor, "copilot_draft_created", "care_plan_draft", draft.id, None, {"raw_text": body.raw_text, "ai": out})
    db.commit()
    return {**to_dict(draft), "warnings": out.get("warnings", []), "ok": out.get("ok", False)}


class DraftUpdate(BaseModel):
    items: list


@router.put("/careplan/draft/{draft_id}")
def update_draft(draft_id: str, body: DraftUpdate, db=Depends(get_db), actor=Depends(get_actor)):
    require(actor, "doctor")
    d = db.get(CarePlanDraft, draft_id)
    if not d or d.status != "DRAFT":
        raise HTTPException(404, "Draft not found or already decided")
    before = d.items
    d.items = body.items
    audit.log(db, actor, "copilot_draft_edited", "care_plan_draft", d.id, {"items": before}, {"items": body.items})
    db.commit()
    return to_dict(d)


@router.post("/careplan/draft/{draft_id}/approve")
def approve_draft(draft_id: str, db=Depends(get_db), actor=Depends(get_actor)):
    """APPROVAL GATE. Only here do items reach the patient's journey."""
    require(actor, "doctor")
    d = db.get(CarePlanDraft, draft_id)
    if not d or d.status != "DRAFT":
        raise HTTPException(404, "Draft not found or already decided")
    created = []
    for it in d.items:
        item = CarePlanItem(patient_id=d.patient_id, type=it["type"], title=it["title"],
                            details=it.get("details", {}), start_date=it["start_date"],
                            end_date=it.get("end_date"), recurrence=it.get("recurrence"),
                            approved_by=actor.user_id)
        db.add(item)
        db.flush()
        # TODO(Samprada): expand recurrence into multiple CareEvents
        ev = CareEvent(patient_id=d.patient_id, type=item.type, title=item.title, details=item.details,
                       scheduled_at=datetime.fromisoformat(item.start_date), source="copilot_approved",
                       care_plan_item_id=item.id)
        db.add(ev)
        created.append(ev)
    d.status = "APPROVED"
    audit.log(db, actor, "care_plan_approved", "care_plan_draft", d.id, None, {"n_items": len(d.items)})
    db.commit()
    return [to_dict(e) for e in created]


@router.get("/patients/{pid}/careplan")
def get_careplan(pid: str, db=Depends(get_db)):
    return [to_dict(x) for x in db.query(CarePlanItem).filter_by(patient_id=pid)]
