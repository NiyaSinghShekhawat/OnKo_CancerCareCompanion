"""Caregiver consent lifecycle: Invite → Accept → Assign responsibilities → Revoke → Re-invite (owner: Samprada).
DB is test_onko.db (set in conftest.py), reseeded before every test — never onko.db."""
import pytest
from fastapi.testclient import TestClient

from core import seed
from core.db import SessionLocal
from core.models import AuditLog, Caregiver
from main import app
from whatsapp import messages

c = TestClient(app)

DOCTOR = {"X-Role": "doctor", "X-User-Id": "doc_mehta"}
NURSE = {"X-Role": "care_team", "X-User-Id": "nurse_anita"}
CONSENT_ACTIONS = ("caregiver_invited", "caregiver_consent_accepted", "caregiver_consent_revoked", "caregiver_reinvited")


def patient(pid):
    return {"X-Role": "patient", "X-User-Id": pid}


def as_cg(cid):
    return {"X-Role": "caregiver", "X-User-Id": cid}


def cg_id(name):
    s = SessionLocal()
    cid = s.query(Caregiver).filter_by(name=name).one().id
    s.close()
    return cid


def status_of(cid):
    s = SessionLocal()
    st = s.get(Caregiver, cid).consent_status
    s.close()
    return st


def consent_audit(cid):
    s = SessionLocal()
    rows = [(a.action, a.actor_id, a.before, a.after) for a in
            s.query(AuditLog).filter_by(entity_id=cid).filter(AuditLog.action.in_(CONSENT_ACTIONS))
            .order_by(AuditLog.timestamp)]
    s.close()
    return rows


def post(cid, step, headers):
    return c.post(f"/caregivers/{cid}/{step}", headers=headers)


@pytest.fixture(autouse=True)
def fresh_db():
    seed.run()
    messages._recent_sos.clear()


# Seed: Sunita Kumar → Rajesh (GRANTED), Karthik Sundaram → Priya (PENDING), Ayesha Ali → Farhan (GRANTED).

# ---------- the whole lifecycle ----------

def test_full_lifecycle_with_audit():
    r = c.post("/patients/p_rajesh/caregivers", headers=patient("p_rajesh"),
               json={"name": "Ravi Kumar", "relation": "Son", "phone_whatsapp": "whatsapp:+910000000099"})
    cid = r.json()["id"]
    assert r.json()["consent_status"] == "PENDING"
    assert c.get(f"/caregivers/{cid}/view", headers=as_cg(cid)).status_code == 403          # not yet

    assert post(cid, "accept", as_cg(cid)).json()["consent_status"] == "GRANTED"
    assert c.get(f"/caregivers/{cid}/view", headers=as_cg(cid)).status_code == 200

    assert post(cid, "revoke", patient("p_rajesh")).json()["consent_status"] == "REVOKED"
    assert c.get(f"/caregivers/{cid}/view", headers=as_cg(cid)).status_code == 403
    r = post(cid, "accept", as_cg(cid))
    assert r.status_code == 409 and r.json()["detail"] == "Consent was revoked; the patient must re-invite"

    assert post(cid, "reinvite", NURSE).json()["consent_status"] == "PENDING"
    assert post(cid, "accept", as_cg(cid)).json()["consent_status"] == "GRANTED"

    assert [(a, actor, before, after) for a, actor, before, after in consent_audit(cid)] == [
        ("caregiver_invited", "p_rajesh", None, {"name": "Ravi Kumar", "relation": "Son",
                                                 "phone_whatsapp": "whatsapp:+910000000099", "type": "family"}),
        ("caregiver_consent_accepted", cid, {"consent_status": "PENDING"}, {"consent_status": "GRANTED"}),
        ("caregiver_consent_revoked", "p_rajesh", {"consent_status": "GRANTED"}, {"consent_status": "REVOKED"}),
        ("caregiver_reinvited", "nurse_anita", {"consent_status": "REVOKED"}, {"consent_status": "PENDING"}),
        ("caregiver_consent_accepted", cid, {"consent_status": "PENDING"}, {"consent_status": "GRANTED"}),
    ]


# ---------- accept ----------

def test_only_the_invited_caregiver_can_accept():
    karthik = cg_id("Karthik Sundaram")
    for headers in (as_cg(cg_id("Sunita Kumar")), DOCTOR, NURSE, patient("p_priya")):
        assert post(karthik, "accept", headers).status_code == 403
    assert status_of(karthik) == "PENDING"
    assert post(karthik, "accept", as_cg(karthik)).status_code == 200
    assert status_of(karthik) == "GRANTED"


def test_accept_when_already_granted_is_a_no_op():
    sunita = cg_id("Sunita Kumar")
    r = post(sunita, "accept", as_cg(sunita))
    assert r.status_code == 200 and r.json()["consent_status"] == "GRANTED"
    assert consent_audit(sunita) == []


def test_accept_unknown_caregiver_404():
    assert post("nope", "accept", as_cg("nope")).status_code == 404


# ---------- revoke ----------

@pytest.mark.parametrize("who, allowed", [("rajesh", True), ("doctor", True), ("care_team", True),
                                          ("another patient", False), ("the caregiver", False),
                                          ("another caregiver", False)])
def test_who_can_revoke(who, allowed):
    sunita = cg_id("Sunita Kumar")
    headers = {"rajesh": patient("p_rajesh"), "doctor": DOCTOR, "care_team": NURSE,
               "another patient": patient("p_priya"), "the caregiver": as_cg(sunita),
               "another caregiver": as_cg(cg_id("Ayesha Ali"))}[who]
    assert post(sunita, "revoke", headers).status_code == (200 if allowed else 403)
    assert status_of(sunita) == ("REVOKED" if allowed else "GRANTED")


def test_revoke_from_pending_and_revoke_twice():
    karthik = cg_id("Karthik Sundaram")
    assert post(karthik, "revoke", patient("p_priya")).json()["consent_status"] == "REVOKED"
    assert post(karthik, "revoke", DOCTOR).status_code == 200            # already revoked: no-op
    assert [a for a, *_ in consent_audit(karthik)] == ["caregiver_consent_revoked"]


def test_revoke_unknown_caregiver_404():
    assert post("nope", "revoke", DOCTOR).status_code == 404


def test_revoke_takes_effect_immediately_everywhere(capsys):
    sunita = cg_id("Sunita Kumar")
    assert c.get("/patients/p_rajesh/checklist/today", headers=as_cg(sunita)).status_code == 200
    post(sunita, "revoke", patient("p_rajesh"))
    assert c.get("/patients/p_rajesh/checklist/today", headers=as_cg(sunita)).status_code == 403
    assert c.get(f"/caregivers/{sunita}/view", headers=as_cg(sunita)).status_code == 403
    assert c.post("/sos", json={"patient_id": "p_rajesh", "channel": "app"}, headers=as_cg(sunita)).status_code == 403
    capsys.readouterr()
    assert c.post("/sos", json={"patient_id": "p_rajesh", "channel": "app"}, headers=patient("p_rajesh")).status_code == 200
    assert "whatsapp:+910000000010" not in capsys.readouterr().out    # Sunita no longer gets SOS alerts


# ---------- reinvite ----------

def test_reinvite_only_from_revoked():
    sunita = cg_id("Sunita Kumar")
    r = post(sunita, "reinvite", patient("p_rajesh"))
    assert r.status_code == 409 and status_of(sunita) == "GRANTED"
    karthik = cg_id("Karthik Sundaram")
    assert post(karthik, "reinvite", patient("p_priya")).json()["consent_status"] == "PENDING"   # no-op
    assert consent_audit(karthik) == []


@pytest.mark.parametrize("who, allowed", [("rajesh", True), ("doctor", True), ("care_team", True),
                                          ("another patient", False), ("the caregiver", False)])
def test_who_can_reinvite(who, allowed):
    sunita = cg_id("Sunita Kumar")
    post(sunita, "revoke", DOCTOR)
    headers = {"rajesh": patient("p_rajesh"), "doctor": DOCTOR, "care_team": NURSE,
               "another patient": patient("p_priya"), "the caregiver": as_cg(sunita)}[who]
    assert post(sunita, "reinvite", headers).status_code == (200 if allowed else 403)
    assert status_of(sunita) == ("PENDING" if allowed else "REVOKED")


# ---------- PATCH is for permissions only ----------

@pytest.mark.parametrize("body", [{"consent_status": "GRANTED"},
                                  {"consent_status": "REVOKED", "permissions": {"view_journey": False}}])
def test_patch_rejects_consent_status(body):
    karthik = cg_id("Karthik Sundaram")
    r = c.patch(f"/caregivers/{karthik}", json=body, headers=DOCTOR)
    assert r.status_code == 400
    assert all(route in r.json()["detail"] for route in ("/accept", "/revoke", "/reinvite"))
    assert status_of(karthik) == "PENDING"


def test_patch_still_assigns_permissions_with_audit():
    sunita = cg_id("Sunita Kumar")
    perms = {"view_journey": True, "upload_reports": False, "receive_escalations": True}
    r = c.patch(f"/caregivers/{sunita}", json={"permissions": perms}, headers=patient("p_rajesh"))
    assert r.status_code == 200 and r.json()["permissions"] == perms and r.json()["consent_status"] == "GRANTED"
    s = SessionLocal()
    (log,) = s.query(AuditLog).filter_by(entity_id=sunita, action="caregiver_updated").all()
    assert log.after == {"permissions": perms}
    s.close()
