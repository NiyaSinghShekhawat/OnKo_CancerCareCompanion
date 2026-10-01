"""DECEASED / TRANSFER_OF_CARE pause the checklist and attention; ACTIVE_TREATMENT / RELAPSE resume (owner: Samprada).
DB is test_onko.db (set in conftest.py), reseeded before every test — never onko.db."""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from core import seed
from core.db import SessionLocal
from core.models import AttentionItem, AuditLog, CareEvent, Patient, PatientQuery
from core.services import attention, journey_state
from main import app

c = TestClient(app)
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


def open_items(pid, label=None):
    return [a for a in c.get("/attention").json() if a["patient_id"] == pid and (label is None or a["label"] == label)]


def checklist(pid):
    r = c.get(f"/patients/{pid}/checklist/today")
    assert r.status_code == 200
    return r.json()


def add_stale_event(db, pid) -> str:
    """An unanswered check-in whose 24h window has already passed."""
    e = CareEvent(patient_id=pid, type="MEDICATION", title="Stale check-in",
                  scheduled_at=datetime.utcnow() - timedelta(hours=30), status="UPCOMING")
    db.add(e)
    db.commit()
    return e.id


def status_of(eid):
    s = SessionLocal()
    st = s.get(CareEvent, eid).status
    s.close()
    return st


def age_seeded_query(db, hours=30):
    q = db.query(PatientQuery).filter_by(patient_id="p_rajesh").one()
    q.created_at = datetime.utcnow() - timedelta(hours=hours)
    db.commit()


def close_follow_up(pid="p_arjun"):
    (item,) = open_items(pid, "FOLLOW_UP")
    assert c.patch(f"/attention/{item['id']}", json={"status": "CLOSED"}, headers=DOCTOR).status_code == 200


def upload_report(pid, title):
    r = c.post(f"/patients/{pid}/reports", json={"title": title, "text": "ALT 30", "uploaded_by_role": "caregiver"},
               headers={"X-Role": "care_team", "X-User-Id": "nurse_anita"})
    assert r.status_code == 200


def patient_sos(pid):
    return c.post("/sos", json={"patient_id": pid, "channel": "app"}, headers={"X-Role": "patient", "X-User-Id": pid})


# ---------- state rules live in one place ----------

def test_state_rules():
    assert [s for s in ("ACTIVE_TREATMENT", "RELAPSE", "REMISSION_SURVIVORSHIP", "PALLIATIVE", "TRANSFER_OF_CARE", "DECEASED")
            if journey_state.checklist_paused(s)] == ["TRANSFER_OF_CARE", "DECEASED"]
    assert not journey_state.attention_allowed("DECEASED") and journey_state.attention_allowed("TRANSFER_OF_CARE")
    assert not journey_state.check_in_follow_up_allowed("TRANSFER_OF_CARE")
    assert journey_state.check_in_follow_up_allowed("RELAPSE")


# ---------- DECEASED ----------

def test_deceased_switch_closes_every_open_item_with_audit(db):
    before = open_items("p_rajesh")
    assert {a["label"] for a in before} == {"NEEDS_REVIEW", "QUERY"}
    set_state("p_rajesh", "DECEASED")
    assert open_items("p_rajesh") == []
    for a in before:
        assert db.get(AttentionItem, a["id"]).status == "CLOSED"
        actions = [(x.action, x.actor_id) for x in db.query(AuditLog).filter_by(entity_id=a["id"])]
        assert actions == [("attention_closed", "doc_mehta")]
    assert open_items("p_arjun", "FOLLOW_UP")          # other patients untouched


def test_deceased_checklist_is_paused():
    assert checklist("p_rajesh")["items"]              # seeded items today
    set_state("p_rajesh", "DECEASED")
    out = checklist("p_rajesh")
    assert out["items"] == [] and out["paused"] is True and out["reason"] == "Journey state DECEASED"


def test_deceased_advance_day_marks_nothing_and_raises_nothing(db):
    mine, other = add_stale_event(db, "p_rajesh"), add_stale_event(db, "p_priya")
    age_seeded_query(db)
    set_state("p_rajesh", "DECEASED")
    set_state("p_arjun", "DECEASED")
    r = c.post("/demo/advance-day")
    assert r.json() == {"marked_no_response": 1}       # only Priya's
    assert status_of(mine) == "UPCOMING" and status_of(other) == "NO_RESPONSE"
    assert open_items("p_rajesh") == [] and open_items("p_arjun") == []


def test_deceased_no_new_items_from_any_path(db):
    set_state("p_rajesh", "DECEASED")
    r = patient_sos("p_rajesh")
    assert r.status_code == 409 and "DECEASED" in r.json()["detail"]
    upload_report("p_rajesh", "LFT — 01 Oct")                                   # report is stored...
    eid = db.query(CareEvent).filter_by(patient_id="p_rajesh", status="UPCOMING", type="MEDICATION").first().id
    assert c.patch(f"/events/{eid}/status", json={"status": "REPORTED_MISSED"}, headers=DOCTOR).status_code == 200
    phone = c.get("/patients/p_rajesh").json()["phone_whatsapp"]
    c.post("/whatsapp/webhook", data={"From": phone, "Body": "SOS"})            # automated path
    c.post("/whatsapp/webhook", data={"From": phone, "Body": "this is his daughter, he passed away"})
    assert attention.raise_item(db, db.get(Patient, "p_rajesh"), "QUERY", "x") is None
    assert open_items("p_rajesh") == []                                         # ...but nothing is raised
    assert db.query(AttentionItem).filter_by(patient_id="p_rajesh").filter(AttentionItem.status != "CLOSED").count() == 0


# ---------- TRANSFER_OF_CARE ----------

def test_transfer_keeps_existing_items_open():
    before = {(a["id"], a["status"]) for a in open_items("p_rajesh") + open_items("p_arjun")}
    set_state("p_rajesh", "TRANSFER_OF_CARE")
    set_state("p_arjun", "TRANSFER_OF_CARE")
    assert {(a["id"], a["status"]) for a in open_items("p_rajesh") + open_items("p_arjun")} == before


def test_transfer_checklist_is_paused():
    set_state("p_rajesh", "TRANSFER_OF_CARE")
    out = checklist("p_rajesh")
    assert out["items"] == [] and out["paused"] is True and out["reason"] == "Journey state TRANSFER_OF_CARE"


def test_transfer_advance_day_marks_nothing_and_no_follow_up(db):
    mine = add_stale_event(db, "p_arjun")
    close_follow_up()
    set_state("p_arjun", "TRANSFER_OF_CARE")
    assert c.post("/demo/advance-day").json() == {"marked_no_response": 0}
    assert status_of(mine) == "UPCOMING"
    assert open_items("p_arjun", "FOLLOW_UP") == []


def test_transfer_queries_reports_and_sos_still_raise(db):
    age_seeded_query(db)
    set_state("p_rajesh", "TRANSFER_OF_CARE")
    c.post("/demo/advance-day")
    assert any(r.startswith("Query unresolved for 30h:") for a in open_items("p_rajesh", "QUERY") for r in a["reasons"])
    upload_report("p_rajesh", "LFT — 01 Oct")
    assert attention.report_reason("LFT — 01 Oct") in open_items("p_rajesh", "NEEDS_REVIEW")[0]["reasons"]
    r = patient_sos("p_rajesh")
    assert r.status_code == 200 and r.json()["label"] == "SOS"


# ---------- resuming ----------

@pytest.mark.parametrize("paused", ["DECEASED", "TRANSFER_OF_CARE"])
@pytest.mark.parametrize("resumed", ["ACTIVE_TREATMENT", "RELAPSE"])
def test_switching_back_resumes_everything(db, paused, resumed):
    close_follow_up()
    set_state("p_arjun", paused)
    set_state("p_arjun", resumed)
    out = checklist("p_arjun")
    assert out["paused"] is False and out["reason"] is None
    stale = add_stale_event(db, "p_arjun")
    c.post("/demo/advance-day")
    assert status_of(stale) == "NO_RESPONSE"
    assert any(attention.STREAK_TEXT in r for a in open_items("p_arjun", "FOLLOW_UP") for r in a["reasons"])
    assert patient_sos("p_arjun").status_code == 200
    upload_report("p_arjun", "CBC — 01 Oct")
    assert attention.report_reason("CBC — 01 Oct") in open_items("p_arjun", "NEEDS_REVIEW")[0]["reasons"]


def test_active_checklist_is_not_paused():
    out = checklist("p_rajesh")
    assert out["paused"] is False and out["reason"] is None and len(out["items"]) == 3
