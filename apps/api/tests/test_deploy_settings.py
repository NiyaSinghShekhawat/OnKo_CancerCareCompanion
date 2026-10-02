"""Deployment switches: DEMO_ACCESS_CODE and DEMO_ROUTES_ENABLED (owner: Samprada).
DB is test_onko.db (set in conftest.py), reseeded before every test — never onko.db.
conftest.py turns both switches off; each test here turns them on with monkeypatch."""
import pytest
from fastapi.testclient import TestClient

from core import seed
from main import app
from whatsapp import messages

c = TestClient(app)
CODE = "onko-demo-2026"
DOCTOR = {"X-Role": "doctor", "X-User-Id": "doc_mehta"}
PATIENT = {"X-Role": "patient", "X-User-Id": "p_rajesh"}
SUNITA = {"X-Role": "caregiver", "X-User-Id": "cg_sunita"}


@pytest.fixture(autouse=True)
def fresh_db():
    seed.run()
    messages._recent_sos.clear()


@pytest.fixture
def code_on(monkeypatch):
    monkeypatch.setenv("DEMO_ACCESS_CODE", CODE)


def with_code(headers, code=CODE):
    return {**headers, "X-Access-Code": code}


# ---------- DEMO_ACCESS_CODE ----------

@pytest.mark.parametrize("value", [None, ""])
def test_no_access_code_configured_means_no_check(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("DEMO_ACCESS_CODE", raising=False)
    else:
        monkeypatch.setenv("DEMO_ACCESS_CODE", value)
    assert c.get("/patients", headers=DOCTOR).status_code == 200


@pytest.mark.parametrize("path, headers", [("/patients", DOCTOR), ("/patients/p_rajesh/checklist/today", PATIENT),
                                           ("/caregivers/cg_sunita/view", SUNITA), ("/attention/mine", DOCTOR)])
def test_code_required_on_every_actor_route(code_on, path, headers):
    for sent in (headers, with_code(headers, "wrong"), with_code(headers, CODE.upper()), with_code(headers, "")):
        r = c.get(path, headers=sent)
        assert r.status_code == 401 and r.json()["detail"] == "Access code required"
    assert c.get(path, headers=with_code(headers)).status_code == 200


def test_code_checked_before_identity(code_on):
    # wrong code: 401 for the code even with a bad role / unknown user, so nothing about users leaks
    for headers in ({}, {"X-Role": "admin", "X-User-Id": "x"}, {"X-Role": "doctor", "X-User-Id": "nobody"}):
        assert c.get("/patients", headers=headers).json()["detail"] == "Access code required"
    # right code: the usual identity checks follow
    assert c.get("/patients", headers=with_code({})).json()["detail"] == "Missing X-Role / X-User-Id"
    assert c.get("/patients", headers=with_code({"X-Role": "doctor", "X-User-Id": "nobody"})).json()["detail"] == \
        "Unknown user for role"
    assert c.get("/patients", headers=with_code(PATIENT)).status_code == 403


def test_writes_need_the_code_too(code_on):
    body = {"patient_id": "p_rajesh", "channel": "app"}
    assert c.post("/sos", json=body, headers=PATIENT).status_code == 401
    assert c.post("/sos", json=body, headers=with_code(PATIENT)).status_code == 200


def test_whatsapp_internal_calls_work_without_a_code(code_on):
    phone = c.get("/patients/p_rajesh", headers=with_code(DOCTOR)).json()["phone_whatsapp"]
    assert c.post("/whatsapp/webhook", data={"From": phone, "Body": "When is my next appointment?"}).status_code == 200
    assert c.post("/whatsapp/webhook", data={"From": phone, "Body": "SOS"}).status_code == 200
    queue = c.get("/attention", headers=with_code(DOCTOR)).json()
    assert any(a["label"] == "SOS" and a["patient_id"] == "p_rajesh" for a in queue)
    assert any(q["text"] == "When is my next appointment?" for q in c.get("/queries", headers=with_code(DOCTOR)).json())


def test_docs_stay_reachable(code_on):
    assert c.get("/openapi.json").status_code == 200


# ---------- DEMO_ROUTES_ENABLED ----------

@pytest.mark.parametrize("value", ["false", "FALSE", "0", "no", "off", " False "])
def test_demo_routes_hidden_when_disabled(monkeypatch, value):
    monkeypatch.setenv("DEMO_ROUTES_ENABLED", value)
    for path in ("/demo/reset", "/demo/advance-day"):
        assert c.post(path, headers=DOCTOR).status_code == 404
        assert c.post(path).status_code == 404                     # 404 before any auth: no hint the route exists
    assert c.get("/patients", headers=DOCTOR).status_code == 200    # everything else unaffected


@pytest.mark.parametrize("value", [None, "true", "1", "yes", ""])
def test_demo_routes_enabled_by_default(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("DEMO_ROUTES_ENABLED", raising=False)
    else:
        monkeypatch.setenv("DEMO_ROUTES_ENABLED", value)
    assert c.post("/demo/advance-day", headers=DOCTOR).status_code == 200
    assert c.post("/demo/reset", headers=DOCTOR).json() == {"reset": True}


def test_disabled_reset_leaves_data_alone(monkeypatch):
    c.patch("/patients/p_lakshmi/journey-state", json={"state": "RELAPSE", "reason": "t"}, headers=DOCTOR)
    monkeypatch.setenv("DEMO_ROUTES_ENABLED", "false")
    assert c.post("/demo/reset", headers=DOCTOR).status_code == 404
    assert c.get("/patients/p_lakshmi", headers=DOCTOR).json()["journey_state"] == "RELAPSE"


def test_both_switches_together(monkeypatch, code_on):
    monkeypatch.setenv("DEMO_ROUTES_ENABLED", "false")
    assert c.post("/demo/reset", headers=with_code(DOCTOR)).status_code == 404
    monkeypatch.setenv("DEMO_ROUTES_ENABLED", "true")
    assert c.post("/demo/reset", headers=DOCTOR).status_code == 401
    assert c.post("/demo/reset", headers=with_code(DOCTOR)).status_code == 200
