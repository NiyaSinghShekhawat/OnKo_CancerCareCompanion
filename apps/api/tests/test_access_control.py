"""Required auth headers and per-patient access (owner: Samprada).
DB is test_onko.db (set in conftest.py), reseeded before every test — never onko.db."""
import pytest
from fastapi.testclient import TestClient

from core import seed
from core.db import SessionLocal
from core.models import CareEvent, Caregiver
from main import app

c = TestClient(app)   # no default headers: every call states who it is

DOCTOR = {"X-Role": "doctor", "X-User-Id": "doc_mehta"}
NURSE = {"X-Role": "care_team", "X-User-Id": "nurse_anita"}


def patient(pid):
    return {"X-Role": "patient", "X-User-Id": pid}


def caregiver(name):
    s = SessionLocal()
    cid = s.query(Caregiver).filter_by(name=name).one().id
    s.close()
    return {"X-Role": "caregiver", "X-User-Id": cid}


def event_of(pid):
    s = SessionLocal()
    eid = s.query(CareEvent).filter_by(patient_id=pid).filter(CareEvent.status.in_(["UPCOMING", "CURRENT"])).first().id
    s.close()
    return eid


@pytest.fixture(autouse=True)
def fresh_db():
    seed.run()


# Seed: Sunita Kumar = Rajesh's caregiver (GRANTED, all permissions), Karthik Sundaram = Priya's (PENDING),
#       Ayesha Ali = Farhan's (GRANTED).
WHO = {
    "doctor": lambda: DOCTOR,
    "care_team": lambda: NURSE,
    "rajesh himself": lambda: patient("p_rajesh"),
    "another patient": lambda: patient("p_priya"),
    "rajesh's caregiver": lambda: caregiver("Sunita Kumar"),
    "someone else's caregiver": lambda: caregiver("Ayesha Ali"),
}
ALLOWED = {"doctor", "care_team", "rajesh himself", "rajesh's caregiver"}


# ---------- headers ----------

@pytest.mark.parametrize("headers", [{}, {"X-Role": "doctor"}, {"X-User-Id": "doc_mehta"},
                                     {"X-Role": "", "X-User-Id": "doc_mehta"}])
@pytest.mark.parametrize("path", ["/patients", "/patients/p_rajesh", "/attention"])
def test_missing_headers_401(headers, path):
    r = c.get(path, headers=headers)
    assert r.status_code == 401 and r.json()["detail"] == "Missing X-Role / X-User-Id"


def test_unknown_role_400():
    assert c.get("/patients", headers={"X-Role": "admin", "X-User-Id": "x"}).status_code == 400


# ---------- staff-only ----------

@pytest.mark.parametrize("path", ["/patients", "/attention", "/dashboard/overview", "/queries", "/audit"])
@pytest.mark.parametrize("who", list(WHO))
def test_staff_only_reads(path, who):
    expected = 200 if who in {"doctor", "care_team"} else 403
    assert c.get(path, headers=WHO[who]()).status_code == expected


@pytest.mark.parametrize("who", ["rajesh himself", "rajesh's caregiver"])
def test_patients_and_caregivers_cannot_resolve_queries(who):
    qid = c.get("/queries", headers=DOCTOR).json()[0]["id"]
    assert c.patch(f"/queries/{qid}", json={"status": "RESOLVED"}, headers=WHO[who]()).status_code == 403
    assert c.patch(f"/queries/{qid}", json={"status": "RESOLVED"}, headers=NURSE).status_code == 200


def test_advance_day_is_doctor_only():
    assert c.post("/demo/advance-day", headers=NURSE).status_code == 403
    assert c.post("/demo/advance-day", headers=patient("p_rajesh")).status_code == 403
    assert c.post("/demo/advance-day", headers=DOCTOR).status_code == 200


# ---------- per-patient reads ----------

STAFF_AND_SELF = {"doctor", "care_team", "rajesh himself"}
NO_CAREGIVER_READS = ["/patients/p_rajesh", "/patients/p_rajesh/timeline", "/patients/p_rajesh/careplan",
                      "/patients/p_rajesh/reports", "/patients/p_rajesh/caregivers", "/patients/p_rajesh/360"]


@pytest.mark.parametrize("path", NO_CAREGIVER_READS)
@pytest.mark.parametrize("who", list(WHO))
def test_per_patient_reads_exclude_caregivers(path, who):
    assert c.get(path, headers=WHO[who]()).status_code == (200 if who in STAFF_AND_SELF else 403)


@pytest.mark.parametrize("who", list(WHO))
def test_checklist_today_includes_consented_caregiver(who):
    assert c.get("/patients/p_rajesh/checklist/today", headers=WHO[who]()).status_code == (200 if who in ALLOWED else 403)


def test_caregiver_reads_go_through_their_own_minimized_view():
    sunita = caregiver("Sunita Kumar")
    for path in NO_CAREGIVER_READS:
        assert c.get(path, headers=sunita).status_code == 403, path
    view = c.get(f"/caregivers/{sunita['X-User-Id']}/view", headers=sunita)
    assert view.status_code == 200 and view.json()["patient"]["id"] == "p_rajesh"


def test_pending_caregiver_has_no_access():
    karthik = caregiver("Karthik Sundaram")
    assert c.get("/patients/p_priya/checklist/today", headers=karthik).status_code == 403
    assert c.post("/sos", json={"patient_id": "p_priya", "channel": "app"}, headers=karthik).status_code == 403


def test_revoking_consent_removes_access_immediately():
    sunita = caregiver("Sunita Kumar")
    cid = sunita["X-User-Id"]
    assert c.get("/patients/p_rajesh/checklist/today", headers=sunita).status_code == 200
    assert c.get(f"/caregivers/{cid}/view", headers=sunita).status_code == 200
    c.patch(f"/caregivers/{cid}", json={"consent_status": "REVOKED"}, headers=patient("p_rajesh"))
    assert c.get("/patients/p_rajesh/checklist/today", headers=sunita).status_code == 403
    assert c.get(f"/caregivers/{cid}/view", headers=sunita).status_code == 403


def test_unknown_patient_is_404_for_staff_and_403_for_others():
    assert c.get("/patients/p_nobody", headers=DOCTOR).status_code == 404
    assert c.get("/patients/p_nobody", headers=patient("p_rajesh")).status_code == 403


# ---------- per-patient writes ----------

@pytest.mark.parametrize("who", list(WHO))
def test_post_query(who):
    r = c.post("/queries", json={"patient_id": "p_rajesh", "text": "When is my next appointment?", "channel": "app"},
               headers=WHO[who]())
    assert r.status_code == (200 if who in ALLOWED else 403)


@pytest.mark.parametrize("who", list(WHO))
def test_post_sos(who):
    r = c.post("/sos", json={"patient_id": "p_rajesh", "channel": "app"}, headers=WHO[who]())
    assert r.status_code == (200 if who in ALLOWED else 403)


@pytest.mark.parametrize("who", list(WHO))
def test_event_status_checks_the_events_patient(who):
    r = c.patch(f"/events/{event_of('p_rajesh')}/status", json={"status": "COMPLETED"}, headers=WHO[who]())
    assert r.status_code == (200 if who in ALLOWED else 403)


def test_event_status_unknown_event_404():
    assert c.patch("/events/nope/status", json={"status": "COMPLETED"}, headers=patient("p_rajesh")).status_code == 404


@pytest.mark.parametrize("who", list(WHO))
def test_upload_report(who):
    r = c.post("/patients/p_rajesh/reports", json={"title": "LFT", "text": "ALT 30", "uploaded_by_role": "patient"},
               headers=WHO[who]())
    assert r.status_code == (200 if who in ALLOWED else 403)


# ---------- minimized event shape for caregivers ----------

MINIMIZED = {"id", "type", "title", "scheduled_at", "status"}


def test_checklist_items_are_minimized_for_caregivers_only():
    sunita = caregiver("Sunita Kumar")
    as_cg = c.get("/patients/p_rajesh/checklist/today", headers=sunita).json()["items"]
    assert as_cg and all(set(e) == MINIMIZED for e in as_cg)
    assert "Dexamethasone" not in str(as_cg)                      # chemo pre-medication instructions are details
    for who in ("doctor", "care_team", "rajesh himself"):
        full = c.get("/patients/p_rajesh/checklist/today", headers=WHO[who]()).json()["items"]
        assert [e["id"] for e in full] == [e["id"] for e in as_cg]
        assert all({"details", "journey_chapter", "source"} <= set(e) for e in full)
        assert "Dexamethasone" in str(full)


@pytest.mark.parametrize("who, minimized", [("rajesh's caregiver", True), ("rajesh himself", False),
                                            ("doctor", False), ("care_team", False)])
def test_status_update_response_shape(who, minimized):
    r = c.patch(f"/events/{event_of('p_rajesh')}/status", json={"status": "COMPLETED"}, headers=WHO[who]())
    assert r.status_code == 200 and r.json()["status"] == "COMPLETED"
    assert (set(r.json()) == MINIMIZED) is minimized
    if not minimized:
        assert "details" in r.json()


def test_caregiver_sees_the_same_event_shape_everywhere():
    sunita = caregiver("Sunita Kumar")
    checklist = {e["id"]: e for e in c.get("/patients/p_rajesh/checklist/today", headers=sunita).json()["items"]}
    view = {e["id"]: e for e in c.get(f"/caregivers/{sunita['X-User-Id']}/view", headers=sunita).json()["upcoming"]}
    shared = checklist.keys() & view.keys()
    assert shared and all(checklist[i] == view[i] for i in shared)
    eid = next(iter(shared))
    updated = c.patch(f"/events/{eid}/status", json={"status": "COMPLETED"}, headers=sunita).json()
    assert updated == {**checklist[eid], "status": "COMPLETED"}


def test_caregiver_can_upload_but_not_read_reports():
    sunita = caregiver("Sunita Kumar")
    r = c.post("/patients/p_rajesh/reports", json={"title": "LFT", "text": "ALT 30", "uploaded_by_role": "caregiver"},
               headers=sunita)
    assert r.status_code == 200
    assert c.get("/patients/p_rajesh/reports", headers=sunita).status_code == 403


def test_caregiver_without_upload_permission_still_refused():
    sunita = caregiver("Sunita Kumar")
    c.patch(f"/caregivers/{sunita['X-User-Id']}", headers=DOCTOR, json={"permissions": {
        "view_journey": True, "upload_reports": False, "receive_escalations": True}})
    r = c.post("/patients/p_rajesh/reports", json={"title": "LFT", "text": "ALT 30"}, headers=sunita)
    assert r.status_code == 403 and r.json()["detail"] == "Caregiver has no upload permission"


# ---------- managing caregivers ----------

def test_caregiver_cannot_change_own_permissions_or_invite():
    sunita = caregiver("Sunita Kumar")
    cid = sunita["X-User-Id"]
    assert c.patch(f"/caregivers/{cid}", json={"consent_status": "GRANTED"}, headers=sunita).status_code == 403
    invite = {"name": "Ravi Kumar", "relation": "Son", "phone_whatsapp": "whatsapp:+910000000099"}
    assert c.post("/patients/p_rajesh/caregivers", json=invite, headers=sunita).status_code == 403
    assert c.post("/patients/p_rajesh/caregivers", json=invite, headers=patient("p_priya")).status_code == 403
    assert c.post("/patients/p_rajesh/caregivers", json=invite, headers=patient("p_rajesh")).status_code == 200
    assert c.patch(f"/caregivers/{cid}", json={"consent_status": "GRANTED"}, headers=patient("p_priya")).status_code == 403
    assert c.patch(f"/caregivers/{cid}", json={"consent_status": "GRANTED"}, headers=NURSE).status_code == 200


# ---------- whatsapp/ builds Actor("patient", id) directly, with no HTTP headers ----------

def test_whatsapp_internal_calls_still_work():
    phone = c.get("/patients/p_rajesh", headers=DOCTOR).json()["phone_whatsapp"]
    c.post("/whatsapp/send-checklist/p_rajesh")
    assert c.post("/whatsapp/webhook", data={"From": phone, "Body": "1 done"}).status_code == 200
    assert c.post("/whatsapp/webhook", data={"From": phone, "Body": "When is my next appointment?"}).status_code == 200
    assert c.post("/whatsapp/webhook", data={"From": phone, "Body": "SOS"}).status_code == 200
    statuses = {e["title"]: e["status"] for e in c.get("/patients/p_rajesh/checklist/today", headers=DOCTOR).json()["items"]}
    assert statuses["Chemotherapy Cycle 4 (Day 1)"] == "COMPLETED"
    assert any(q["text"] == "When is my next appointment?" for q in c.get("/queries", headers=DOCTOR).json())
    assert any(a["label"] == "SOS" and a["patient_id"] == "p_rajesh" for a in c.get("/attention", headers=DOCTOR).json())
