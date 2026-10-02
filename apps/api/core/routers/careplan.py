"""Care Plan Copilot routes. AI output is only ever a DRAFT until the doctor approves."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.db import get_db
from core.auth import get_actor, require, require_patient_access
from core.models import Patient, CarePlanDraft, CarePlanItem, CareEvent
from core.serialize import to_dict
from core.services import audit, recurrence
from ai.copilot import structure_care_plan, end_date_for

router = APIRouter(tags=["careplan"])

_MUTABLE_FUTURE_STATUSES = {"UPCOMING", "CURRENT", "RESCHEDULED"}
_VALID_TYPES = {"MEDICATION", "INVESTIGATION", "TREATMENT", "APPOINTMENT", "MILESTONE"}


def _valid_iso(value) -> bool:
    try:
        datetime.fromisoformat(value)
        return True
    except (TypeError, ValueError):
        return False


def _body_updates(body: BaseModel) -> dict:
    """Pydantic v1/v2 compatible exclude-unset payload."""
    if hasattr(body, "model_dump"):
        return body.model_dump(exclude_unset=True)
    return body.dict(exclude_unset=True)


def _future_mutable_events(db, item_id: str, now: datetime) -> list[CareEvent]:
    return db.query(CareEvent).filter(
        CareEvent.care_plan_item_id == item_id,
        CareEvent.scheduled_at >= now,
        CareEvent.status.in_(_MUTABLE_FUTURE_STATUSES),
    ).all()


def _validate_item_fields(item: CarePlanItem):
    if item.type not in _VALID_TYPES:
        raise HTTPException(400, "Unknown care-plan item type")
    if not item.title or not item.title.strip():
        raise HTTPException(400, "Care-plan item title is required")
    if not _valid_iso(item.start_date):
        raise HTTPException(400, "Set a valid start date")
    if item.end_date and not _valid_iso(item.end_date):
        raise HTTPException(400, "Set a valid end date")
    if item.end_date and datetime.fromisoformat(item.end_date) < datetime.fromisoformat(item.start_date):
        raise HTTPException(400, "End date cannot be before start date")
    if item.recurrence and recurrence.parse(item.recurrence) is None:
        raise HTTPException(400, "Unsupported recurrence. Use 'daily HH:MM[, HH:MM ...]' or 'every N days'.")


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
    missing = [it.get("title") or "untitled item" for it in d.items if not _valid_iso(it.get("start_date"))]
    if missing:
        raise HTTPException(400, f"Set a start date for: {', '.join(missing)}")
    for it in d.items:
        if not it.get("end_date"):
            it["end_date"] = end_date_for(it)
    created = []
    for it in d.items:
        item = CarePlanItem(patient_id=d.patient_id, type=it["type"], title=it["title"],
                            details=it.get("details", {}), start_date=it["start_date"],
                            end_date=it.get("end_date"), recurrence=it.get("recurrence"),
                            approved_by=actor.user_id)
        db.add(item)
        db.flush()
        for when in recurrence.expand(item.start_date, item.end_date, item.recurrence):
            ev = CareEvent(patient_id=d.patient_id, type=item.type, title=item.title, details=item.details,
                           scheduled_at=when, source="copilot_approved", care_plan_item_id=item.id)
            db.add(ev)
            created.append(ev)
    d.status = "APPROVED"
    audit.log(db, actor, "care_plan_approved", "care_plan_draft", d.id, None,
              {"n_items": len(d.items), "n_events": len(created)})
    db.commit()
    return [to_dict(e) for e in created]


class CarePlanItemUpdate(BaseModel):
    type: str | None = None
    title: str | None = None
    details: dict | None = None
    start_date: str | None = None
    end_date: str | None = None
    recurrence: str | None = None


@router.patch("/careplan/items/{item_id}")
def update_careplan_item(item_id: str, body: CarePlanItemUpdate, db=Depends(get_db), actor=Depends(get_actor)):
    """Doctor edits an approved item. Recorded history stays; only future mutable events are rebuilt."""
    require(actor, "doctor")
    item = db.get(CarePlanItem, item_id)
    if not item:
        raise HTTPException(404, "Care-plan item not found")

    before = to_dict(item)
    updates = _body_updates(body)
    for field, value in updates.items():
        if field == "details" and value is None:
            value = {}
        setattr(item, field, value)

    _validate_item_fields(item)

    now = datetime.utcnow()
    future = _future_mutable_events(db, item.id, now)
    for ev in future:
        db.delete(ev)

    regenerated = 0
    for when in recurrence.expand(item.start_date, item.end_date, item.recurrence):
        if when < now:
            continue
        db.add(CareEvent(
            patient_id=item.patient_id,
            type=item.type,
            title=item.title,
            details=item.details,
            scheduled_at=when,
            source="careplan_edited",
            care_plan_item_id=item.id,
        ))
        regenerated += 1

    db.flush()
    after = to_dict(item)
    audit.log(
        db, actor, "care_plan_item_edited", "care_plan_item", item.id,
        before,
        {**after, "future_events_removed": len(future), "future_events_regenerated": regenerated},
    )
    db.commit()
    return to_dict(item)


@router.delete("/careplan/items/{item_id}")
def delete_careplan_item(item_id: str, db=Depends(get_db), actor=Depends(get_actor)):
    """Remove an item from the active plan without erasing already-recorded patient activity."""
    require(actor, "doctor")
    item = db.get(CarePlanItem, item_id)
    if not item:
        raise HTTPException(404, "Care-plan item not found")

    before = to_dict(item)
    now = datetime.utcnow()
    future = _future_mutable_events(db, item.id, now)
    for ev in future:
        db.delete(ev)

    historical = db.query(CareEvent).filter(CareEvent.care_plan_item_id == item.id).all()
    for ev in historical:
        ev.care_plan_item_id = None

    audit.log(
        db, actor, "care_plan_item_removed", "care_plan_item", item.id,
        before,
        {
            "removed_from_active_plan": True,
            "future_events_removed": len(future),
            "historical_events_preserved": len(historical),
        },
    )
    patient_id = item.patient_id
    db.delete(item)
    db.commit()
    return {
        "id": item_id,
        "patient_id": patient_id,
        "removed": True,
        "future_events_removed": len(future),
        "historical_events_preserved": len(historical),
    }


@router.get("/patients/{pid}/careplan")
def get_careplan(pid: str, db=Depends(get_db), actor=Depends(get_actor)):
    require_patient_access(actor, pid, db, allow_caregivers=False)
    return [to_dict(x) for x in db.query(CarePlanItem).filter_by(patient_id=pid)]
