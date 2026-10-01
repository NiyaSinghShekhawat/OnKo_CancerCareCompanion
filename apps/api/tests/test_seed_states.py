"""Seed has one patient per journey state, and each behaves as the state rules say (owner: Samprada).
DB is test_onko.db (set in conftest.py), reseeded before every test — never onko.db."""
import re
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from core import seed
from core.db import SessionLocal
from core.models import AttentionItem, CarePlanDraft, CareEvent, Caregiver, Patient, PatientQuery
from core.services import attention
from main import app

c = TestClient(app, headers={"X-Role": "doctor", "X-User-Id": "doc_mehta"})   # auth headers are required; per-request headers override
DOCTOR = {"X-Role": "doctor", "X-User-Id": "doc_mehta"}
NEW = {"p_meera": "PALLIATIVE", "p_vikram": "TRANSFER_OF_CARE", "p_farhan": "RELAPSE", "p_kamala": "DECEASED"}
INTERPRETATION = re.compile(r"worsen|improv|concern(?!\s+logged)|risk|severe|critical|deteriorat|prognos|terminal|"
                            r"anaemi|anemi|abnormal|poor|dying|end[- ]stage", re.IGNORECASE)


@pytest.fixture(autouse=True)
def fresh_db():
    seed.run()


@pytest.fixture
def db():
    s = SessionLocal()
    yield s
    s.close()


def items(pid, label=None, open_only=True):
    s = SessionLocal()
    q = s.query(AttentionItem).filter_by(patient_id=pid)
    if open_only:
        q = q.filter(AttentionItem.status.in_(["PENDING", "ACKNOWLEDGED"]))
    if label:
        q = q.filter_by(label=label)
    out = [(a.label, list(a.reasons), a.status) for a in q]
    s.close()
    return out


def checklist(pid):
    return c.get(f"/patients/{pid}/checklist/today").json()


def timeline(pid):
    return c.get(f"/patients/{pid}/timeline").json()


def patient_sos(pid):
    return c.post("/sos", json={"patient_id": pid, "channel": "app"}, headers={"X-Role": "patient", "X-User-Id": pid})


def snapshot(db):
    return sorted((a.patient_id, a.label, tuple(a.reasons), a.status) for a in db.query(AttentionItem))


# ---------- shape of the seed ----------

def test_one_patient_per_journey_state_and_originals_kept(db):
    states = {p.id: p.journey_state for p in db.query(Patient)}
    assert len(states) == 8
    assert set(states.values()) == {"ACTIVE_TREATMENT", "REMISSION_SURVIVORSHIP", "PALLIATIVE",
                                    "TRANSFER_OF_CARE", "RELAPSE", "DECEASED"}
    assert {pid: states[pid] for pid in NEW} == NEW
    assert {"p_rajesh", "p_priya", "p_arjun", "p_lakshmi"} <= set(states)


def test_new_patients_have_complete_consistent_profiles(db):
    for pid, state in NEW.items():
        p = db.get(Patient, pid)
        assert p.diagnosis_label.endswith("(as recorded)")
        assert p.preferred_language in {"English", "Hindi", "Tamil", "Telugu"}   # languages the WhatsApp copy supports
        assert p.age and p.gender in {"M", "F"}
        assert re.fullmatch(r"whatsapp:\+9100000000\d\d", p.phone_whatsapp)
        assert p.previous_journey_state and p.previous_journey_state != state
        assert p.journey_state_changed_at < datetime.utcnow()
        (cg,) = db.query(Caregiver).filter_by(patient_id=pid).all()
        assert cg.consent_status == "GRANTED" and cg.type == "family"
        assert re.fullmatch(r"whatsapp:\+9100000000\d\d", cg.phone_whatsapp)


def test_whatsapp_numbers_are_unique(db):
    numbers = [p.phone_whatsapp for p in db.query(Patient)] + [g.phone_whatsapp for g in db.query(Caregiver)]
    assert len(numbers) == len(set(numbers))


def test_no_interpretation_words_in_seeded_text(db):
    texts = []
    for pid in NEW:
        p = db.get(Patient, pid)
        texts += [p.diagnosis_label, p.regimen_label]
        texts += [e.title for e in db.query(CareEvent).filter_by(patient_id=pid)]
        texts += [x for q in db.query(PatientQuery).filter_by(patient_id=pid) for x in (q.text, q.summary)]
    texts += [r for a in db.query(AttentionItem) for r in a.reasons]
    assert [t for t in texts if t and INTERPRETATION.search(t)] == []


def test_seeded_attention_is_what_the_rules_produce(db):
    before = snapshot(db)
    for pid in NEW:
        attention.recompute_for_patient(db, db.get(Patient, pid))
    db.commit()
    assert snapshot(db) == before


# ---------- Meera: PALLIATIVE ----------

def test_meera_missed_dose_raises_nothing_but_query_does(db):
    assert db.query(CareEvent).filter_by(patient_id="p_meera", status="REPORTED_MISSED").count() == 1
    q = db.query(PatientQuery).filter_by(patient_id="p_meera").one()
    assert q.status == "OPEN"
    assert items("p_meera") == [("QUERY", [attention.concern_reason(q.summary)], "PENDING")]


def test_meera_stays_quiet_on_adherence(db):
    c.post("/demo/advance-day")
    eid = db.query(CareEvent).filter_by(patient_id="p_meera", status="UPCOMING").first().id
    assert c.patch(f"/events/{eid}/status", json={"status": "REPORTED_MISSED"}, headers=DOCTOR).status_code == 200
    assert {label for label, *_ in items("p_meera")} == {"QUERY"}
    assert checklist("p_meera")["paused"] is False


def test_resolving_meeras_query_closes_her_item(db):
    q = db.query(PatientQuery).filter_by(patient_id="p_meera").one()
    c.patch(f"/queries/{q.id}", json={"status": "RESOLVED"}, headers=DOCTOR)
    assert items("p_meera") == []


# ---------- Vikram: TRANSFER_OF_CARE ----------

def test_vikram_checklist_paused_despite_events_today(db):
    today = datetime.utcnow().date()
    assert any(e.scheduled_at.date() == today for e in db.query(CareEvent).filter_by(patient_id="p_vikram"))
    out = checklist("p_vikram")
    assert out["items"] == [] and out["paused"] is True and out["reason"] == "Journey state TRANSFER_OF_CARE"


def test_vikram_has_upcoming_events_that_are_never_marked(db):
    upcoming = [e for e in timeline("p_vikram") if e["status"] == "UPCOMING"]
    assert len(upcoming) >= 3
    c.post("/demo/advance-day")
    assert [e["status"] for e in timeline("p_vikram") if e["id"] in {u["id"] for u in upcoming}] == ["UPCOMING"] * len(upcoming)
    assert items("p_vikram") == []


def test_vikram_sos_still_raises():
    assert patient_sos("p_vikram").status_code == 200
    assert [label for label, *_ in items("p_vikram")] == ["SOS"]


# ---------- Farhan: RELAPSE ----------

def test_farhan_has_two_chapters_split_at_the_relapse(db):
    p = db.get(Patient, "p_farhan")
    assert p.journey_chapter == 2 and p.previous_journey_state == "REMISSION_SURVIVORSHIP"
    tl = timeline("p_farhan")
    assert [e["scheduled_at"] for e in tl] == sorted(e["scheduled_at"] for e in tl)
    ch1 = [e for e in tl if e["journey_chapter"] == 1]
    ch2 = [e for e in tl if e["journey_chapter"] == 2]
    assert ch1 and ch2 and len(ch1) + len(ch2) == len(tl)
    assert {e["status"] for e in ch1} == {"COMPLETED"}
    changed = p.journey_state_changed_at.isoformat()
    assert all(e["scheduled_at"] < changed for e in ch1) and all(e["scheduled_at"] > changed for e in ch2)
    assert any(e["status"] == "UPCOMING" for e in ch2)
    assert c.get("/patients/p_farhan/360").json()["timeline"] == tl


def test_farhan_new_care_plan_lands_in_chapter_2(db):
    d = CarePlanDraft(patient_id="p_farhan", raw_text="x", created_by="doc_mehta", items=[
        {"type": "MEDICATION", "title": "Prednisolone 20mg", "start_date": datetime.utcnow().date().isoformat(),
         "end_date": None, "recurrence": None}])
    db.add(d)
    db.commit()
    created = c.post(f"/careplan/draft/{d.id}/approve", headers=DOCTOR).json()
    assert [e["journey_chapter"] for e in created] == [2]


def test_farhan_is_active_for_checklist_and_attention():
    assert checklist("p_farhan")["paused"] is False
    assert items("p_farhan") == []


# ---------- Kamala: DECEASED ----------

def test_kamala_completed_history_only_and_no_attention_ever(db):
    tl = timeline("p_kamala")
    assert tl and {e["status"] for e in tl} == {"COMPLETED"}
    assert items("p_kamala", open_only=False) == []


def test_kamala_is_a_hard_stop():
    out = checklist("p_kamala")
    assert out["items"] == [] and out["paused"] is True and out["reason"] == "Journey state DECEASED"
    assert patient_sos("p_kamala").status_code == 409
    c.post("/demo/advance-day")
    assert items("p_kamala", open_only=False) == []
