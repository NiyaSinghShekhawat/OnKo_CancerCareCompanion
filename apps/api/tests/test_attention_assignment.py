"""Attention queue: assignment, nurse / junior-doctor handoff, filters, /attention/mine (owner: Samprada).
DB is test_onko.db (set in conftest.py), reseeded before every test — never onko.db."""
import pytest
from fastapi.testclient import TestClient

from core import seed
from core.db import SessionLocal
from core.models import AttentionItem, AuditLog, User
from main import app

c = TestClient(app)
DOCTOR = {"X-Role": "doctor", "X-User-Id": "doc_mehta"}
ANITA = {"X-Role": "care_team", "X-User-Id": "nurse_anita"}
RAVI = {"X-Role": "care_team", "X-User-Id": "nurse_ravi"}
ASSIGN_ACTIONS = ("attention_assigned", "attention_handoff", "attention_update")


@pytest.fixture(autouse=True)
def fresh_db():
    seed.run()
    s = SessionLocal()
    s.add(User(id="nurse_ravi", name="Nurse Ravi", role="care_team"))   # a second nurse to hand off between
    s.commit()
    s.close()


def item_id(pid, label):
    s = SessionLocal()
    aid = s.query(AttentionItem).filter_by(patient_id=pid, label=label).one().id
    s.close()
    return aid


def item(aid):
    s = SessionLocal()
    a = s.get(AttentionItem, aid)
    s.close()
    return a


def audit_trail(aid):
    s = SessionLocal()
    rows = [(a.action, a.actor_id, a.before, a.after) for a in s.query(AuditLog)
            .filter_by(entity_id=aid).filter(AuditLog.action.in_(ASSIGN_ACTIONS)).order_by(AuditLog.timestamp)]
    s.close()
    return rows


def patch(aid, body, headers=DOCTOR):
    return c.patch(f"/attention/{aid}", json=body, headers=headers)


def ids(resp):
    assert resp.status_code == 200
    return {(a["patient_id"], a["label"]) for a in resp.json()}


# ---------- seed + /attention/mine ----------

def test_seed_assigns_arjuns_follow_up_to_nurse_anita():
    assert item(item_id("p_arjun", "FOLLOW_UP")).assigned_to == "nurse_anita"
    assert ids(c.get("/attention/mine", headers=ANITA)) == {("p_arjun", "FOLLOW_UP")}
    assert ids(c.get("/attention/mine", headers=DOCTOR)) == set()
    assert ids(c.get("/attention/mine", headers=RAVI)) == set()


def test_mine_leaves_out_closed_items():
    patch(item_id("p_arjun", "FOLLOW_UP"), {"status": "CLOSED"}, headers=ANITA)
    assert c.get("/attention/mine", headers=ANITA).json() == []


@pytest.mark.parametrize("headers", [{"X-Role": "patient", "X-User-Id": "p_rajesh"},
                                     {"X-Role": "caregiver", "X-User-Id": "cg_sunita"}])
def test_queue_routes_are_staff_only(headers):
    assert c.get("/attention/mine", headers=headers).status_code == 403
    assert c.get("/attention?label=QUERY", headers=headers).status_code == 403


# ---------- filters ----------

def test_filters():
    q = lambda params: ids(c.get(f"/attention?{params}", headers=DOCTOR))
    everything = q("")
    assert everything == {("p_rajesh", "NEEDS_REVIEW"), ("p_rajesh", "QUERY"), ("p_arjun", "FOLLOW_UP"),
                          ("p_meera", "QUERY")}
    assert q("assigned_to=nurse_anita") == {("p_arjun", "FOLLOW_UP")}
    assert q("label=QUERY") == {("p_rajesh", "QUERY"), ("p_meera", "QUERY")}
    assert q("patient_id=p_rajesh") == {("p_rajesh", "NEEDS_REVIEW"), ("p_rajesh", "QUERY")}
    assert q("patient_id=p_rajesh&label=QUERY") == {("p_rajesh", "QUERY")}
    assert q("status=PENDING") == everything
    assert q("assigned_to=nurse_ravi") == set()


def test_closed_only_with_status_filter():
    aid = item_id("p_rajesh", "QUERY")
    patch(aid, {"status": "CLOSED"})
    assert ("p_rajesh", "QUERY") not in ids(c.get("/attention", headers=DOCTOR))
    assert ids(c.get("/attention?status=CLOSED", headers=DOCTOR)) == {("p_rajesh", "QUERY")}


def test_filtered_queue_keeps_priority_order():
    labels = [a["label"] for a in c.get("/attention?status=PENDING", headers=DOCTOR).json()]
    order = ["SOS", "NEEDS_REVIEW", "QUERY", "FOLLOW_UP"]
    assert labels == sorted(labels, key=order.index)


@pytest.mark.parametrize("params", ["label=URGENT", "status=OPEN"])
def test_unknown_filter_values_400(params):
    assert c.get(f"/attention?{params}", headers=DOCTOR).status_code == 400


# ---------- assigning and handing off ----------

def test_assigning_an_unassigned_item():
    aid = item_id("p_rajesh", "NEEDS_REVIEW")
    r = patch(aid, {"assigned_to": "nurse_anita"})
    assert r.status_code == 200 and r.json()["assigned_to"] == "nurse_anita" and r.json()["status"] == "PENDING"
    assert audit_trail(aid) == [("attention_assigned", "doc_mehta", {"assigned_to": None}, {"assigned_to": "nurse_anita"})]


def test_handoff_records_old_and_new_assignee():
    aid = item_id("p_arjun", "FOLLOW_UP")
    assert patch(aid, {"assigned_to": "nurse_ravi"}, headers=ANITA).status_code == 200      # nurse → nurse
    assert patch(aid, {"assigned_to": "doc_mehta"}).status_code == 200                       # nurse → doctor
    assert audit_trail(aid) == [
        ("attention_handoff", "nurse_anita", {"assigned_to": "nurse_anita"}, {"assigned_to": "nurse_ravi"}),
        ("attention_handoff", "doc_mehta", {"assigned_to": "nurse_ravi"}, {"assigned_to": "doc_mehta"}),
    ]
    assert ids(c.get("/attention/mine", headers=DOCTOR)) == {("p_arjun", "FOLLOW_UP")}
    assert c.get("/attention/mine", headers=ANITA).json() == []


def test_same_assignee_again_writes_nothing():
    aid = item_id("p_arjun", "FOLLOW_UP")
    assert patch(aid, {"assigned_to": "nurse_anita"}).status_code == 200
    assert audit_trail(aid) == []


@pytest.mark.parametrize("assignee", ["nobody", "p_rajesh", "cg_sunita"])
def test_assignee_must_be_doctor_or_care_team(assignee):
    aid = item_id("p_rajesh", "NEEDS_REVIEW")
    r = patch(aid, {"assigned_to": assignee, "status": "ACKNOWLEDGED"})
    assert r.status_code == 400
    a = item(aid)
    assert (a.assigned_to, a.status) == (None, "PENDING")       # nothing applied
    assert audit_trail(aid) == []


def test_status_and_assignment_in_one_call_audit_both():
    aid = item_id("p_rajesh", "QUERY")
    patch(aid, {"status": "ACKNOWLEDGED", "assigned_to": "nurse_anita"})
    assert audit_trail(aid) == [
        ("attention_update", "doc_mehta", {"status": "PENDING"}, {"status": "ACKNOWLEDGED"}),
        ("attention_assigned", "doc_mehta", {"assigned_to": None}, {"assigned_to": "nurse_anita"}),
    ]


# ---------- who may change what ----------

def test_care_team_changes_own_and_unassigned_items():
    assert patch(item_id("p_arjun", "FOLLOW_UP"), {"status": "ACKNOWLEDGED"}, headers=ANITA).status_code == 200
    assert patch(item_id("p_rajesh", "QUERY"), {"status": "ACKNOWLEDGED"}, headers=ANITA).status_code == 200


def test_care_team_cannot_touch_someone_elses_item():
    aid = item_id("p_arjun", "FOLLOW_UP")                       # assigned to Anita
    for body in ({"status": "CLOSED"}, {"assigned_to": "nurse_ravi"}):
        r = patch(aid, body, headers=RAVI)
        assert r.status_code == 403 and r.json()["detail"] == "This item is assigned to someone else"
    a = item(aid)
    assert (a.assigned_to, a.status) == ("nurse_anita", "PENDING")


def test_nurse_who_hands_off_loses_control_doctor_keeps_it():
    aid = item_id("p_arjun", "FOLLOW_UP")
    patch(aid, {"assigned_to": "doc_mehta"}, headers=ANITA)
    assert patch(aid, {"status": "CLOSED"}, headers=ANITA).status_code == 403
    assert patch(aid, {"status": "CLOSED"}, headers=DOCTOR).status_code == 200


def test_doctor_changes_any_item():
    aid = item_id("p_arjun", "FOLLOW_UP")                       # assigned to Anita, not the doctor
    assert patch(aid, {"status": "HANDLED"}).status_code == 200
    assert item(aid).status == "HANDLED"


def test_unknown_item_404():
    assert patch("nope", {"status": "CLOSED"}).status_code == 404
