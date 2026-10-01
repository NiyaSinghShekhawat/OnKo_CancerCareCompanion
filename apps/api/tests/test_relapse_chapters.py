"""RELAPSE starts a new journey chapter; history is kept (owner: Samprada).
DB is test_onko.db (set in conftest.py), reseeded before every test — never onko.db."""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from core import seed
from core.db import SessionLocal
from core.models import AuditLog, CarePlanDraft, CareEvent, Patient
from main import app

c = TestClient(app, headers={"X-Role": "doctor", "X-User-Id": "doc_mehta"})   # auth headers are required; per-request headers override
DOCTOR = {"X-Role": "doctor", "X-User-Id": "doc_mehta"}


@pytest.fixture(autouse=True)
def fresh_db():
    seed.run()


@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()


def set_state(pid, state):
    r = c.patch(f"/patients/{pid}/journey-state", json={"state": state, "reason": "test"}, headers=DOCTOR)
    assert r.status_code == 200
    return r.json()


def chapter(pid):
    return c.get(f"/patients/{pid}").json()["journey_chapter"]


def timeline(pid):
    return c.get(f"/patients/{pid}/timeline").json()


def approve_plan(db, pid, start: str, title="Capecitabine (new regimen)", recurrence="daily 09:00", end=None):
    d = CarePlanDraft(patient_id=pid, raw_text="x", created_by="doc_mehta", items=[
        {"type": "MEDICATION", "title": title, "start_date": start, "end_date": end, "recurrence": recurrence}])
    db.add(d)
    db.commit()
    r = c.post(f"/careplan/draft/{d.id}/approve", headers=DOCTOR)
    assert r.status_code == 200
    return r.json()


def day(days_from_today: int) -> str:
    return (datetime.utcnow() + timedelta(days=days_from_today)).date().isoformat()


def test_seed_is_chapter_1_except_the_relapse_patient(db):
    """p_farhan is seeded in RELAPSE, chapter 2 (see test_seed_states.py)."""
    assert {p.journey_chapter for p in db.query(Patient).filter(Patient.id != "p_farhan")} == {1}
    assert {e.journey_chapter for e in db.query(CareEvent).filter(CareEvent.patient_id != "p_farhan")} == {1}
    assert all(e["journey_chapter"] == 1 for e in timeline("p_rajesh"))


def test_relapse_increments_chapter_with_audit(db):
    assert set_state("p_rajesh", "RELAPSE")["journey_chapter"] == 2
    logs = [(a.action, a.before, a.after) for a in db.query(AuditLog).filter_by(entity_id="p_rajesh").order_by(AuditLog.timestamp)]
    assert ("journey_chapter_started", {"journey_chapter": 1}, {"journey_chapter": 2, "state": "RELAPSE"}) in logs
    assert [a for a, *_ in logs].count("journey_state_change") == 1


def test_only_a_real_switch_to_relapse_increments():
    set_state("p_rajesh", "RELAPSE")
    set_state("p_rajesh", "RELAPSE")                          # same state again: no new chapter
    assert chapter("p_rajesh") == 2
    for state in ("ACTIVE_TREATMENT", "PALLIATIVE", "TRANSFER_OF_CARE", "REMISSION_SURVIVORSHIP"):
        set_state("p_rajesh", state)
    assert chapter("p_rajesh") == 2
    set_state("p_rajesh", "RELAPSE")                          # second relapse
    assert chapter("p_rajesh") == 3
    assert chapter("p_priya") == 1                            # other patients untouched


def test_old_events_keep_their_chapter_and_are_not_deleted(db):
    before = {e["id"]: e for e in timeline("p_rajesh")}
    set_state("p_rajesh", "RELAPSE")
    after = {e["id"]: e for e in timeline("p_rajesh")}
    assert after == before                                    # same events, same chapter, same everything


def test_care_plan_approval_after_relapse_uses_new_chapter(db):
    set_state("p_rajesh", "RELAPSE")
    created = approve_plan(db, "p_rajesh", day(1), end=day(3))
    assert len(created) == 3 and {e["journey_chapter"] for e in created} == {2}


def test_care_plan_approval_before_relapse_stays_in_chapter_1(db):
    created = approve_plan(db, "p_rajesh", day(1))
    set_state("p_rajesh", "RELAPSE")
    ids = {e["id"] for e in created}
    assert {e["journey_chapter"] for e in timeline("p_rajesh") if e["id"] in ids} == {1}


def test_any_other_creation_path_gets_current_chapter(db):
    set_state("p_rajesh", "RELAPSE")
    set_state("p_rajesh", "ACTIVE_TREATMENT")
    set_state("p_rajesh", "RELAPSE")
    e = CareEvent(patient_id="p_rajesh", type="APPOINTMENT", title="Created elsewhere", scheduled_at=datetime.utcnow())
    explicit = CareEvent(patient_id="p_rajesh", type="APPOINTMENT", title="Explicit", scheduled_at=datetime.utcnow(),
                         journey_chapter=1)
    db.add_all([e, explicit])
    db.commit()
    assert (e.journey_chapter, explicit.journey_chapter) == (3, 1)


def test_timeline_has_all_chapters_sorted_by_date(db):
    set_state("p_rajesh", "RELAPSE")
    approve_plan(db, "p_rajesh", day(1), title="Chapter 2 dose")   # dated before the chapter-1 teleconsult (day +2)
    tl = timeline("p_rajesh")
    assert [e["scheduled_at"] for e in tl] == sorted(e["scheduled_at"] for e in tl)
    assert {e["journey_chapter"] for e in tl} == {1, 2}
    titles = [e["title"] for e in tl]
    assert titles.index("Chapter 2 dose") < titles.index("Teleconsult with Dr. Mehta")
    assert c.get("/patients/p_rajesh/360").json()["timeline"] == tl


def test_init_db_adds_chapter_columns_with_value_1(db):
    from sqlalchemy import inspect, text
    from core.db import engine, init_db
    db.close()
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE patients DROP COLUMN journey_chapter"))
        conn.execute(text("ALTER TABLE care_events DROP COLUMN journey_chapter"))
    init_db()
    for table in ("patients", "care_events"):
        assert "journey_chapter" in {col["name"] for col in inspect(engine).get_columns(table)}
    assert chapter("p_rajesh") == 1
    assert {e["journey_chapter"] for e in timeline("p_rajesh")} == {1}
