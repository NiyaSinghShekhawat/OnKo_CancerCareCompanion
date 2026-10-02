"""PATCH /reports/{id}/reviewed (owner: Samprada).
DB is test_onko.db (set in conftest.py), reseeded before every test — never onko.db."""
import pytest
from fastapi.testclient import TestClient

from core import seed
from core.db import SessionLocal
from core.models import AttentionItem, AuditLog, Report
from core.services import attention
from main import app

c = TestClient(app, headers={"X-Role": "doctor", "X-User-Id": "doc_mehta"})   # auth headers are required; per-request headers override
DOCTOR = {"X-Role": "doctor", "X-User-Id": "doc_mehta"}
NURSE = {"X-Role": "care_team", "X-User-Id": "nurse_anita"}
MISSED = "Medication reported missed: Capecitabine evening dose"


@pytest.fixture(autouse=True)
def fresh_db():
    seed.run()


@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()


def seeded_report_id(db) -> str:
    return db.query(Report).filter_by(patient_id="p_rajesh").one().id


def needs_review(patient_id="p_rajesh"):
    return [a for a in c.get("/attention").json() if a["label"] == "NEEDS_REVIEW" and a["patient_id"] == patient_id]


def audit_actions(db, entity_id):
    return [(a.action, a.actor_id) for a in db.query(AuditLog).filter_by(entity_id=entity_id).order_by(AuditLog.timestamp)]


def upload(title, pid="p_priya"):
    r = c.post(f"/patients/{pid}/reports", json={"title": title, "text": "WBC 4.1", "uploaded_by_role": "patient"},
               headers={"X-Role": "patient", "X-User-Id": pid})
    assert r.status_code == 200
    return r.json()["id"]


def test_doctor_marks_reviewed_and_reason_is_cleared(db):
    rid = seeded_report_id(db)
    r = c.patch(f"/reports/{rid}/reviewed", headers=DOCTOR)
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == rid and body["reviewed"] is True and body["title"] == "CBC — 20 Sep"
    (item,) = needs_review()
    assert item["reasons"] == [MISSED] and item["status"] == "PENDING"
    assert audit_actions(db, rid) == [("report_reviewed", "doc_mehta")]
    assert audit_actions(db, item["id"]) == [("attention_reason_cleared", "doc_mehta")]


def test_care_team_can_mark_reviewed(db):
    assert c.patch(f"/reports/{seeded_report_id(db)}/reviewed", headers=NURSE).json()["reviewed"] is True


@pytest.mark.parametrize("role", ["patient", "caregiver"])
def test_other_roles_refused_and_nothing_changes(db, role):
    rid = seeded_report_id(db)
    r = c.patch(f"/reports/{rid}/reviewed", headers={"X-Role": role, "X-User-Id": "x"})
    assert r.status_code == 403
    assert db.get(Report, rid).reviewed is False
    assert attention.report_reason("CBC — 20 Sep") in needs_review()[0]["reasons"]
    assert audit_actions(db, rid) == []


def test_unknown_report_is_404():
    assert c.patch("/reports/nope/reviewed", headers=DOCTOR).status_code == 404


def test_second_call_is_a_no_op(db):
    rid = seeded_report_id(db)
    c.patch(f"/reports/{rid}/reviewed", headers=DOCTOR)
    n_audits = db.query(AuditLog).count()
    r = c.patch(f"/reports/{rid}/reviewed", headers=NURSE)
    assert r.status_code == 200 and r.json()["reviewed"] is True
    assert db.query(AuditLog).count() == n_audits


def test_last_reason_closes_the_item(db):
    rid = upload("LFT — 30 Sep")
    (item,) = needs_review("p_priya")
    assert item["reasons"] == [attention.report_reason("LFT — 30 Sep")]
    c.patch(f"/reports/{rid}/reviewed", headers=DOCTOR)
    assert needs_review("p_priya") == []
    assert db.get(AttentionItem, item["id"]).status == "CLOSED"
    assert audit_actions(db, item["id"]) == [("attention_closed", "doc_mehta")]


def test_only_that_reports_reason_is_cleared():
    first, second = upload("LFT — 30 Sep"), upload("KFT — 30 Sep")
    c.patch(f"/reports/{first}/reviewed", headers=DOCTOR)
    (item,) = needs_review("p_priya")
    assert item["reasons"] == [attention.report_reason("KFT — 30 Sep")]


def test_advance_day_does_not_re_raise_reviewed_report(db):
    c.patch(f"/reports/{seeded_report_id(db)}/reviewed", headers=DOCTOR)
    c.post("/demo/advance-day", headers=DOCTOR)
    assert needs_review()[0]["reasons"] == [MISSED]


def test_dashboard_pending_count_drops(db):
    before = c.get("/dashboard/overview").json()["reports_pending_review"]
    c.patch(f"/reports/{seeded_report_id(db)}/reviewed", headers=DOCTOR)
    assert c.get("/dashboard/overview").json()["reports_pending_review"] == before - 1
