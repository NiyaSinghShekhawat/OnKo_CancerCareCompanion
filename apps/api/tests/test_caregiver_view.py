"""GET /caregivers/{id}/view — caregiver-scoped view with data minimization (owner: Samprada).
DB is test_onko.db (set in conftest.py), reseeded before every test — never onko.db."""
import json
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from core import seed
from core.db import SessionLocal
from core.models import AuditLog, CareEvent, Caregiver
from main import app

c = TestClient(app, headers={"X-Role": "doctor", "X-User-Id": "doc_mehta"})   # auth headers are required; per-request headers override
DOCTOR = {"X-Role": "doctor", "X-User-Id": "doc_mehta"}
EVENT_KEYS = {"id", "type", "title", "scheduled_at", "status"}


@pytest.fixture(autouse=True)
def fresh_db():
    seed.run()


@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()


def cg_id(db, name):
    return db.query(Caregiver).filter_by(name=name).one().id


def as_caregiver(cid):
    return {"X-Role": "caregiver", "X-User-Id": cid}


def view(cid, headers=None):
    return c.get(f"/caregivers/{cid}/view", headers=headers or as_caregiver(cid))


def add_event(db, pid, title, hours_from_now, status):
    db.add(CareEvent(patient_id=pid, type="MEDICATION", title=title, details={"dose": "SECRET-DOSE"},
                     scheduled_at=datetime.utcnow() + timedelta(hours=hours_from_now), status=status))
    db.commit()


def titles(events):
    return [e["title"] for e in events]


# ---------- what is returned ----------

def test_caregiver_sees_only_the_minimized_shape(db):
    r = view(cg_id(db, "Sunita Kumar"))
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"patient", "upcoming", "recent", "can_upload_reports", "receives_escalations"}
    assert body["patient"] == {"id": "p_rajesh", "name": "Rajesh Kumar", "journey_state": "ACTIVE_TREATMENT",
                               "preferred_language": "Hindi"}
    for e in body["upcoming"] + body["recent"]:
        assert set(e) == EVENT_KEYS
    raw = json.dumps(body)
    for leaked in ("Adenocarcinoma", "diagnosis", "details", "dose", "Dexamethasone",   # diagnosis, event details
                   "nausea", "CBC — 20 Sep", "Haemoglobin",                            # query, report
                   "reasons", "NEEDS_REVIEW", "abha", "phone_whatsapp"):                # attention, identifiers
        assert leaked not in raw


def test_upcoming_and_recent_windows(db):
    add_event(db, "p_rajesh", "In 6 days", 6 * 24, "UPCOMING")
    add_event(db, "p_rajesh", "In 8 days", 8 * 24, "UPCOMING")
    add_event(db, "p_rajesh", "Done 6 days ago", -6 * 24, "COMPLETED")
    add_event(db, "p_rajesh", "Done 8 days ago", -8 * 24, "COMPLETED")
    add_event(db, "p_rajesh", "No reply 2 days ago", -2 * 24, "NO_RESPONSE")
    add_event(db, "p_rajesh", "Rescheduled yesterday", -24, "RESCHEDULED")
    body = view(cg_id(db, "Sunita Kumar")).json()

    up = titles(body["upcoming"])
    assert "In 6 days" in up and "Teleconsult with Dr. Mehta" in up
    assert "In 8 days" not in up and "Rescheduled yesterday" not in up
    assert "Chemotherapy Cycle 4 (Day 1)" in up            # today's open item, even if its time has passed
    assert [e["scheduled_at"] for e in body["upcoming"]] == sorted(e["scheduled_at"] for e in body["upcoming"])

    rec = body["recent"]
    assert {e["status"] for e in rec} <= {"COMPLETED", "REPORTED_MISSED", "NO_RESPONSE"}
    assert {"Done 6 days ago", "No reply 2 days ago", "Capecitabine 500mg", "CBC"} <= set(titles(rec))
    assert "Done 8 days ago" not in titles(rec) and "Rescheduled yesterday" not in titles(rec)
    assert [e["scheduled_at"] for e in rec] == sorted((e["scheduled_at"] for e in rec), reverse=True)   # newest first


def test_permission_flags(db):
    cid = cg_id(db, "Sunita Kumar")
    b = view(cid).json()
    assert (b["can_upload_reports"], b["receives_escalations"]) == (True, True)
    c.patch(f"/caregivers/{cid}", json={"permissions": {"view_journey": True, "upload_reports": False,
                                                        "receive_escalations": False}}, headers=DOCTOR)
    b = view(cid).json()
    assert (b["can_upload_reports"], b["receives_escalations"]) == (False, False)


def test_doctor_can_open_any_caregiver_view(db):
    assert view(cg_id(db, "Ayesha Ali"), headers=DOCTOR).json()["patient"]["id"] == "p_farhan"


# ---------- who may call ----------

def test_caregiver_cannot_open_another_caregivers_view(db):
    r = view(cg_id(db, "Sunita Kumar"), headers=as_caregiver(cg_id(db, "Ayesha Ali")))
    assert r.status_code == 403


@pytest.mark.parametrize("role", ["patient", "care_team"])
def test_other_roles_refused(db, role):
    cid = cg_id(db, "Sunita Kumar")
    assert view(cid, headers={"X-Role": role, "X-User-Id": cid}).status_code == 403


def test_unknown_caregiver_is_404():
    assert view("nope", headers=DOCTOR).status_code == 404


# ---------- consent ----------

def test_pending_consent_refused(db):
    r = view(cg_id(db, "Karthik Sundaram"))                    # seeded PENDING
    assert r.status_code == 403 and r.json()["detail"] == "Caregiver access not granted"


@pytest.mark.parametrize("change", ["revoke", "no view_journey"])
def test_revoked_or_no_view_journey_refused_even_for_doctor(db, change):
    cid = cg_id(db, "Sunita Kumar")
    if change == "revoke":
        assert c.post(f"/caregivers/{cid}/revoke", headers=DOCTOR).status_code == 200
    else:
        c.patch(f"/caregivers/{cid}", headers=DOCTOR, json={"permissions": {
            "view_journey": False, "upload_reports": True, "receive_escalations": True}})
    for headers in (as_caregiver(cid), DOCTOR):
        r = view(cid, headers=headers)
        assert r.status_code == 403 and r.json()["detail"] == "Caregiver access not granted"


# ---------- journey state ----------

def test_deceased_patient_has_no_upcoming_but_keeps_recent(db):
    cid = cg_id(db, "Sunita Kumar")
    assert view(cid).json()["upcoming"]
    c.patch("/patients/p_rajesh/journey-state", json={"state": "DECEASED", "reason": "test"}, headers=DOCTOR)
    body = view(cid).json()
    assert body["upcoming"] == [] and body["recent"] and body["patient"]["journey_state"] == "DECEASED"


def test_seeded_deceased_patient_view(db):
    body = view(cg_id(db, "Suresh Rao")).json()
    assert body["patient"]["id"] == "p_kamala" and body["upcoming"] == []


# ---------- audit ----------

def test_each_successful_call_is_audited_and_refusals_are_not(db):
    cid, pending = cg_id(db, "Sunita Kumar"), cg_id(db, "Karthik Sundaram")
    view(cid)
    view(cid, headers=DOCTOR)
    view(pending)
    view(cid, headers={"X-Role": "patient", "X-User-Id": "p_rajesh"})
    logs = db.query(AuditLog).filter_by(action="caregiver_view_accessed").order_by(AuditLog.timestamp).all()
    assert [(a.entity_id, a.actor_role, a.actor_id, a.after) for a in logs] == [
        (cid, "caregiver", cid, {"patient_id": "p_rajesh"}),
        (cid, "doctor", "doc_mehta", {"patient_id": "p_rajesh"}),
    ]
