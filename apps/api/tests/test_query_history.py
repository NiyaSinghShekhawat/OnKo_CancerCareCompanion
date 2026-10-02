"""Query queue/history behavior.

Resolved queries leave the active Patient360 queue but remain available in query_history with the recorded response.
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


def test_resolved_query_leaves_open_queue_but_stays_in_history():
    before = c.get("/patients/p_rajesh/360", headers=DOCTOR)
    assert before.status_code == 200
    open_queries = before.json()["open_queries"]
    assert open_queries

    query_id = open_queries[0]["id"]
    response_text = "Your care team has reviewed this message. Please follow the instructions already provided by your clinician."

    updated = c.patch(
        f"/queries/{query_id}",
        headers=DOCTOR,
        json={"status": "RESOLVED", "response": response_text},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "RESOLVED"
    assert updated.json()["response"] == response_text

    after = c.get("/patients/p_rajesh/360", headers=DOCTOR)
    assert after.status_code == 200
    body = after.json()

    assert all(q["id"] != query_id for q in body["open_queries"])
    historical = next(q for q in body["query_history"] if q["id"] == query_id)
    assert historical["status"] == "RESOLVED"
    assert historical["response"] == response_text
