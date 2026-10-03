"""Clearing attention reasons when a query is resolved or a report is reviewed (owner: Samprada).
DB is test_onko.db (set in conftest.py), reseeded before every test — never onko.db."""
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from core import seed
from core.auth import Actor
from core.db import SessionLocal
from core.models import AttentionItem, AuditLog, CareEvent, Patient, PatientQuery, Report
from core.services import attention
from core.timeutil import utcnow
from main import app

c = TestClient(app, headers={"X-Role": "doctor", "X-User-Id": "doc_mehta"})   # auth headers are required; per-request headers override
NURSE = {"X-Role": "care_team", "X-User-Id": "nurse_anita"}
DOCTOR = Actor("doctor", "doc_mehta")


@pytest.fixture(autouse=True)
def fresh_db():
    seed.run()


@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()


def add_item(db, label, reasons, patient_id="p_priya", status="PENDING") -> str:
    p = db.get(Patient, patient_id)
    item = AttentionItem(patient_id=p.id, patient_name=p.name, label=label, reasons=reasons, status=status)
    db.add(item)
    db.commit()
    return item.id


def item(aid):
    s = SessionLocal()
    a = s.get(AttentionItem, aid)
    s.close()
    return a


def audits(db, aid):
    return db.query(AuditLog).filter_by(entity_id=aid).order_by(AuditLog.timestamp).all()


def open_item(label, patient_id):
    return [a for a in c.get("/attention").json() if a["label"] == label and a["patient_id"] == patient_id]


# ---------- clear_reason ----------

def test_clear_reason_removes_only_that_reason(db):
    aid = add_item(db, "NEEDS_REVIEW", ["Medication reported missed: X, 01 Oct", attention.report_reason("CBC")])
    changed = attention.clear_reason(db, db.get(Patient, "p_priya"), "NEEDS_REVIEW", attention.report_reason("CBC"), DOCTOR)
    db.commit()
    assert [a.id for a in changed] == [aid]
    assert item(aid).reasons == ["Medication reported missed: X, 01 Oct"]
    assert item(aid).status == "PENDING"
    assert [a.action for a in audits(db, aid)] == ["attention_reason_cleared"]


def test_clear_last_reason_closes_item_and_audits(db):
    aid = add_item(db, "NEEDS_REVIEW", [attention.report_reason("CBC")], status="ACKNOWLEDGED")
    attention.clear_reason(db, db.get(Patient, "p_priya"), "NEEDS_REVIEW", attention.report_reason("CBC"), DOCTOR)
    db.commit()
    assert item(aid).reasons == [] and item(aid).status == "CLOSED"
    (log,) = audits(db, aid)
    assert log.action == "attention_closed" and log.actor_id == "doc_mehta"
    assert log.before == {"reasons": [attention.report_reason("CBC")], "status": "ACKNOWLEDGED"}
    assert log.after == {"reasons": [], "status": "CLOSED"}


def test_clear_reason_is_exact_match(db):
    aid = add_item(db, "NEEDS_REVIEW", [attention.report_reason("CBC — 20 Sep")])
    assert attention.clear_reason(db, db.get(Patient, "p_priya"), "NEEDS_REVIEW", attention.report_reason("CBC"), DOCTOR) == []
    db.commit()
    assert item(aid).reasons == [attention.report_reason("CBC — 20 Sep")]
    assert audits(db, aid) == []


def test_clear_reason_leaves_other_labels_patients_and_closed_items(db):
    r = attention.report_reason("CBC")
    other_label = add_item(db, "FOLLOW_UP", [r])
    other_patient = add_item(db, "NEEDS_REVIEW", [r], patient_id="p_arjun")
    handled = add_item(db, "NEEDS_REVIEW", [r], status="HANDLED")
    attention.clear_reason(db, db.get(Patient, "p_priya"), "NEEDS_REVIEW", r, DOCTOR)
    db.commit()
    for aid in (other_label, other_patient, handled):
        assert item(aid).reasons == [r]
    assert item(handled).status == "HANDLED"


def test_report_reviewed_clears_seeded_report_reason(db):
    """What the future reports-reviewed route will do."""
    rep = db.query(Report).filter_by(patient_id="p_rajesh").one()
    rep.reviewed = True
    attention.clear_reason(db, db.get(Patient, "p_rajesh"), "NEEDS_REVIEW", attention.report_reason(rep.title), DOCTOR)
    db.commit()
    (left,) = open_item("NEEDS_REVIEW", "p_rajesh")
    missed = db.query(CareEvent).filter_by(patient_id="p_rajesh", status="REPORTED_MISSED").one()
    assert left["reasons"] == [attention.missed_reason(missed)]
    attention.recompute_for_patient(db, db.get(Patient, "p_rajesh"))   # reviewed report is not re-raised
    db.commit()
    assert open_item("NEEDS_REVIEW", "p_rajesh")[0]["reasons"] == left["reasons"]


# ---------- PATCH /queries/{id} ----------

def seeded_query(db):
    return db.query(PatientQuery).filter(PatientQuery.summary.startswith("Patient reports nausea")).one()


def test_resolving_seeded_query_closes_query_item(db):
    q = seeded_query(db)
    (before,) = open_item("QUERY", "p_rajesh")
    assert c.patch(f"/queries/{q.id}", json={"status": "RESOLVED", "response": "Call the ward"}, headers=NURSE).status_code == 200
    assert open_item("QUERY", "p_rajesh") == []
    assert item(before["id"]).status == "CLOSED"
    assert [(a.action, a.actor_id) for a in audits(db, before["id"])] == [("attention_closed", "nurse_anita")]


def test_other_statuses_do_not_clear(db):
    q = seeded_query(db)
    for status in ("IN_REVIEW", "ESCALATED"):
        assert c.patch(f"/queries/{q.id}", json={"status": status}, headers=NURSE).status_code == 200
        assert len(open_item("QUERY", "p_rajesh")[0]["reasons"]) == 1


def test_resolving_one_query_keeps_the_others_reason(db):
    rajesh = db.get(Patient, "p_rajesh")
    other = PatientQuery(patient_id="p_rajesh", text="t", category="MEDICATION", summary="Asks about a missed dose.")
    db.add(other)
    attention.raise_item(db, rajesh, "QUERY", attention.concern_reason(other.summary))
    db.commit()
    c.patch(f"/queries/{seeded_query(db).id}", json={"status": "RESOLVED"}, headers=NURSE)
    (left,) = open_item("QUERY", "p_rajesh")
    assert left["reasons"] == [attention.concern_reason("Asks about a missed dose.")]


def test_resolving_also_clears_unresolved_over_24h_reason(db):
    q = seeded_query(db)
    q.created_at = utcnow() - timedelta(hours=30)
    db.commit()
    c.post("/demo/advance-day")
    reasons = open_item("QUERY", "p_rajesh")[0]["reasons"]
    assert any(r.startswith("Query unresolved for 30h:") for r in reasons)
    c.patch(f"/queries/{q.id}", json={"status": "RESOLVED"}, headers=NURSE)
    assert open_item("QUERY", "p_rajesh") == []
    c.post("/demo/advance-day")   # resolved query is not re-raised
    assert open_item("QUERY", "p_rajesh") == []


def test_resolving_twice_is_a_no_op(db):
    q = seeded_query(db)
    c.patch(f"/queries/{q.id}", json={"status": "RESOLVED"}, headers=NURSE)
    n = db.query(AuditLog).filter_by(action="attention_closed").count()
    assert c.patch(f"/queries/{q.id}", json={"status": "RESOLVED"}, headers=NURSE).status_code == 200
    assert db.query(AuditLog).filter_by(action="attention_closed").count() == n
