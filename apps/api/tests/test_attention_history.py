"""Attention queue/history behavior.

Handled and closed items leave the live attention queue but remain available in Patient 360 history.
"""
import pytest
from fastapi.testclient import TestClient

from core import seed
from main import app

c = TestClient(app)
DOCTOR = {"X-Role": "doctor", "X-User-Id": "doc_mehta"}


@pytest.fixture(autouse=True)
def fresh_db():
    seed.run()


def _seeded_attention():
    items = c.get("/attention", headers=DOCTOR)
    assert items.status_code == 200
    body = items.json()
    assert body
    return body[0]


def test_acknowledged_attention_stays_in_active_queue():
    item = _seeded_attention()

    r = c.patch(
        f"/attention/{item['id']}",
        headers=DOCTOR,
        json={"status": "ACKNOWLEDGED", "assigned_to": "Dr. Rajiv Mehta"},
    )
    assert r.status_code == 200

    active = c.get("/attention", headers=DOCTOR).json()
    updated = next(a for a in active if a["id"] == item["id"])
    assert updated["status"] == "ACKNOWLEDGED"
    assert updated["assigned_to"] == "Dr. Rajiv Mehta"


def test_handled_attention_leaves_queue_but_remains_in_patient_history():
    item = _seeded_attention()

    r = c.patch(
        f"/attention/{item['id']}",
        headers=DOCTOR,
        json={"status": "HANDLED"},
    )
    assert r.status_code == 200

    active = c.get("/attention", headers=DOCTOR).json()
    assert all(a["id"] != item["id"] for a in active)

    p360 = c.get(f"/patients/{item['patient_id']}/360", headers=DOCTOR)
    assert p360.status_code == 200
    body = p360.json()

    assert all(a["id"] != item["id"] for a in body["attention"])
    historical = next(a for a in body["attention_history"] if a["id"] == item["id"])
    assert historical["status"] == "HANDLED"


def test_closed_attention_leaves_queue_but_remains_in_patient_history():
    item = _seeded_attention()

    r = c.patch(
        f"/attention/{item['id']}",
        headers=DOCTOR,
        json={"status": "CLOSED"},
    )
    assert r.status_code == 200

    active = c.get("/attention", headers=DOCTOR).json()
    assert all(a["id"] != item["id"] for a in active)

    history = c.get(f"/patients/{item['patient_id']}/360", headers=DOCTOR).json()["attention_history"]
    closed = next(a for a in history if a["id"] == item["id"])
    assert closed["status"] == "CLOSED"


def test_handled_sos_is_not_counted_as_open_dashboard_sos():
    items = c.get("/attention", headers=DOCTOR).json()
    sos = next((a for a in items if a["label"] == "SOS"), None)
    if sos is None:
        # Seed may have no SOS; create one through the public endpoint.
        created = c.post("/sos", headers=DOCTOR, json={"patient_id": "p_rajesh", "channel": "app"})
        assert created.status_code == 200
        sos = created.json()

    before = c.get("/dashboard/overview", headers=DOCTOR)
    assert before.status_code == 200
    assert before.json()["sos_open"] >= 1

    handled = c.patch(f"/attention/{sos['id']}", headers=DOCTOR, json={"status": "HANDLED"})
    assert handled.status_code == 200

    after = c.get("/dashboard/overview", headers=DOCTOR)
    assert after.status_code == 200
    assert after.json()["sos_open"] == before.json()["sos_open"] - 1
