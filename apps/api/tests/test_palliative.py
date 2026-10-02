"""PALLIATIVE suppresses adherence-style attention (owner: Samprada).
DB is test_onko.db (set in conftest.py), reseeded before every test — never onko.db."""
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from core import seed
from core.db import SessionLocal
from core.models import AttentionItem, AuditLog, CareEvent, PatientQuery, Report
from core.services import attention
from core.timeutil import utcnow
from main import app

c = TestClient(app, headers={"X-Role": "doctor", "X-User-Id": "doc_mehta"})   # auth headers are required; per-request headers override
DOCTOR = {"X-Role": "doctor", "X-User-Id": "doc_mehta"}
MISSED = "Medication reported missed: Capecitabine evening dose"
CBC = attention.report_reason("CBC — 20 Sep")


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


def open_items(pid, label):
    return [a for a in c.get("/attention").json() if a["patient_id"] == pid and a["label"] == label]


def reasons(pid, label):
    return [r for a in open_items(pid, label) for r in a["reasons"]]


def audit_actions(db, entity_id):
    return [(a.action, a.actor_id) for a in db.query(AuditLog).filter_by(entity_id=entity_id).order_by(AuditLog.timestamp)]


def event_id(db, pid, title, status=None):
    q = db.query(CareEvent).filter_by(patient_id=pid, title=title)
    return (q.filter_by(status=status) if status else q).first().id


# ---------- switching to PALLIATIVE ----------

def test_switch_drops_missed_reason_but_keeps_report_reason(db):
    (item,) = open_items("p_rajesh", "NEEDS_REVIEW")
    set_state("p_rajesh", "PALLIATIVE")
    (after,) = open_items("p_rajesh", "NEEDS_REVIEW")
    assert after["id"] == item["id"] and after["reasons"] == [CBC] and after["status"] == "PENDING"
    assert audit_actions(db, item["id"]) == [("attention_reason_cleared", "doc_mehta")]


def test_switch_closes_follow_up(db):
    (item,) = open_items("p_arjun", "FOLLOW_UP")
    set_state("p_arjun", "PALLIATIVE")
    assert open_items("p_arjun", "FOLLOW_UP") == []
    assert db.get(AttentionItem, item["id"]).status == "CLOSED"
    assert audit_actions(db, item["id"]) == [("attention_closed", "doc_mehta")]
    assert ("journey_state_change", "doc_mehta") in audit_actions(db, "p_arjun")


def test_switch_leaves_query_items_alone():
    before = open_items("p_rajesh", "QUERY")
    set_state("p_rajesh", "PALLIATIVE")
    assert open_items("p_rajesh", "QUERY") == before


def test_switch_closes_needs_review_left_with_only_missed_reasons(db):
    report_id = db.query(Report).filter_by(patient_id="p_rajesh").one().id
    c.patch(f"/reports/{report_id}/reviewed", headers=DOCTOR)
    assert reasons("p_rajesh", "NEEDS_REVIEW") == [MISSED]
    set_state("p_rajesh", "PALLIATIVE")
    assert open_items("p_rajesh", "NEEDS_REVIEW") == []


def test_other_states_do_not_suppress():
    for state in ("RELAPSE", "REMISSION_SURVIVORSHIP", "TRANSFER_OF_CARE", "ACTIVE_TREATMENT"):
        set_state("p_arjun", state)
        set_state("p_rajesh", state)
        assert len(open_items("p_arjun", "FOLLOW_UP")) == 1
        assert MISSED in reasons("p_rajesh", "NEEDS_REVIEW")


# ---------- while PALLIATIVE ----------

@pytest.mark.parametrize("title", ["Capecitabine 500mg", "Chemotherapy Cycle 4 (Day 1)"])   # MEDICATION, TREATMENT
def test_reported_missed_raises_nothing(db, title):
    set_state("p_rajesh", "PALLIATIVE")
    eid = event_id(db, "p_rajesh", title, status="UPCOMING" if title.startswith("Cap") else None)
    r = c.patch(f"/events/{eid}/status", json={"status": "REPORTED_MISSED"}, headers=DOCTOR)
    assert r.status_code == 200 and r.json()["status"] == "REPORTED_MISSED"
    assert not any(attention.is_missed_reason(x) for x in reasons("p_rajesh", "NEEDS_REVIEW"))
    assert audit_actions(db, eid) == [("event_status", "doc_mehta")]   # the status change itself is still audited


def test_advance_day_does_not_re_raise_follow_up():
    set_state("p_arjun", "PALLIATIVE")
    c.post("/demo/advance-day")
    assert open_items("p_arjun", "FOLLOW_UP") == []


def test_queries_still_raise(db):
    set_state("p_rajesh", "PALLIATIVE")
    q = db.query(PatientQuery).filter_by(patient_id="p_rajesh").one()
    q.created_at = utcnow() - timedelta(hours=30)
    db.commit()
    c.post("/demo/advance-day")
    assert any(r.startswith("Query unresolved for 30h:") for r in reasons("p_rajesh", "QUERY"))


def test_new_reports_still_raise():
    set_state("p_rajesh", "PALLIATIVE")
    r = c.post("/patients/p_rajesh/reports", json={"title": "LFT — 01 Oct", "text": "ALT 30", "uploaded_by_role": "patient"},
               headers={"X-Role": "patient", "X-User-Id": "p_rajesh"})
    assert r.status_code == 200
    assert attention.report_reason("LFT — 01 Oct") in reasons("p_rajesh", "NEEDS_REVIEW")


def test_sos_still_raises():
    set_state("p_rajesh", "PALLIATIVE")
    r = c.post("/sos", json={"patient_id": "p_rajesh", "channel": "app"}, headers={"X-Role": "patient", "X-User-Id": "p_rajesh"})
    assert r.status_code == 200 and r.json()["label"] == "SOS"
    assert len(open_items("p_rajesh", "SOS")) == 1


# ---------- not PALLIATIVE / leaving PALLIATIVE ----------

def test_active_patient_missed_dose_still_raises(db):
    eid = event_id(db, "p_rajesh", "Capecitabine 500mg", status="UPCOMING")
    c.patch(f"/events/{eid}/status", json={"status": "REPORTED_MISSED"}, headers=DOCTOR)
    assert any(r.startswith("Medication reported missed: Capecitabine 500mg, ") for r in reasons("p_rajesh", "NEEDS_REVIEW"))


def test_leaving_palliative_lets_rules_raise_again():
    set_state("p_arjun", "PALLIATIVE")
    set_state("p_arjun", "ACTIVE_TREATMENT")
    assert open_items("p_arjun", "FOLLOW_UP") == []          # nothing is re-raised just by switching back
    c.post("/demo/advance-day")
    assert any(attention.STREAK_TEXT in r for r in reasons("p_arjun", "FOLLOW_UP"))
