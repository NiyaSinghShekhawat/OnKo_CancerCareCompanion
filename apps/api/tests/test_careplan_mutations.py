"""Approved care-plan mutation tests.

Editing/removing an approved plan item must preserve recorded history while rebuilding/removing
only future mutable events. Tests use test_onko.db via conftest.py.
"""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from core import seed
from core.db import SessionLocal
from core.models import CareEvent, CarePlanItem
from main import app

c = TestClient(app)
DOCTOR = {"X-Role": "doctor", "X-User-Id": "doc_mehta"}
NURSE = {"X-Role": "care_team", "X-User-Id": "nurse_anita"}
PATIENT = {"X-Role": "patient", "X-User-Id": "p_rajesh"}


@pytest.fixture(autouse=True)
def fresh_db():
    seed.run()


def _make_course():
    db = SessionLocal()
    today = datetime.utcnow().date()
    start = today + timedelta(days=1)
    end = today + timedelta(days=2)
    item = CarePlanItem(
        patient_id="p_rajesh",
        type="MEDICATION",
        title="Capecitabine 500mg",
        details={"dose": "500 mg"},
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        recurrence="daily 09:00",
        approved_by="doc_mehta",
    )
    db.add(item)
    db.flush()

    past = CareEvent(
        patient_id="p_rajesh",
        type="MEDICATION",
        title=item.title,
        scheduled_at=datetime.utcnow() - timedelta(days=1),
        status="COMPLETED",
        response_state="COMPLETED",
        source="copilot_approved",
        care_plan_item_id=item.id,
    )
    future = CareEvent(
        patient_id="p_rajesh",
        type="MEDICATION",
        title=item.title,
        scheduled_at=datetime.utcnow() + timedelta(days=1),
        status="UPCOMING",
        source="copilot_approved",
        care_plan_item_id=item.id,
    )
    db.add_all([past, future])
    db.commit()
    iid, past_id, future_id = item.id, past.id, future.id
    db.close()
    return iid, past_id, future_id, start, end


def test_only_doctor_can_edit_or_remove_approved_item():
    item_id, *_ = _make_course()
    patch = {"title": "Updated title"}

    assert c.patch(f"/careplan/items/{item_id}", json=patch, headers=NURSE).status_code == 403
    assert c.patch(f"/careplan/items/{item_id}", json=patch, headers=PATIENT).status_code == 403
    assert c.delete(f"/careplan/items/{item_id}", headers=NURSE).status_code == 403
    assert c.delete(f"/careplan/items/{item_id}", headers=PATIENT).status_code == 403


def test_edit_preserves_history_and_rebuilds_future_events():
    item_id, past_id, future_id, start, end = _make_course()

    r = c.patch(
        f"/careplan/items/{item_id}",
        headers=DOCTOR,
        json={
            "title": "Capecitabine 500mg after food",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "recurrence": "daily 09:00, 21:00",
        },
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Capecitabine 500mg after food"
    assert r.json()["recurrence"] == "daily 09:00, 21:00"

    db = SessionLocal()
    assert db.get(CareEvent, past_id).status == "COMPLETED"
    assert db.get(CareEvent, future_id) is None

    future = (
        db.query(CareEvent)
        .filter_by(care_plan_item_id=item_id)
        .filter(CareEvent.scheduled_at >= datetime.utcnow())
        .all()
    )
    assert len(future) == 4
    assert all(e.title == "Capecitabine 500mg after food" for e in future)
    db.close()


def test_remove_keeps_recorded_history_and_removes_future_schedule():
    item_id, past_id, future_id, *_ = _make_course()

    r = c.delete(f"/careplan/items/{item_id}", headers=DOCTOR)
    assert r.status_code == 200
    assert r.json()["removed"] is True
    assert r.json()["future_events_removed"] == 1
    assert r.json()["historical_events_preserved"] == 1

    db = SessionLocal()
    assert db.get(CarePlanItem, item_id) is None
    assert db.get(CareEvent, future_id) is None

    past = db.get(CareEvent, past_id)
    assert past is not None
    assert past.status == "COMPLETED"
    assert past.care_plan_item_id is None
    db.close()
