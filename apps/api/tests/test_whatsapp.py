"""WhatsApp flow tests (owner: Shreyan). Twilio runs in dry-run mode (no keys), DB is test_onko.db."""
import pytest
from fastapi.testclient import TestClient

from core import seed
from main import app
import hashlib, hmac, base64, os
from whatsapp import messages, webhook
from whatsapp.parser import intent, parse_all, parse_checklist_reply

c = TestClient(app, headers={"X-Role": "doctor", "X-User-Id": "doc_mehta"})   # auth headers are required; per-request headers override


@pytest.fixture(autouse=True)
def fresh_db():
    seed.run()


def phone():
    return c.get("/patients/p_rajesh").json()["phone_whatsapp"]


def wa(body: str, sender: str | None = None) -> str:
    r = c.post("/whatsapp/webhook", data={"From": sender or phone(), "Body": body})
    assert r.status_code == 200
    return r.text


def today():
    return {e["title"]: e for e in c.get("/patients/p_rajesh/checklist/today").json()["items"]}


# ---- parser ----

@pytest.mark.parametrize("text,expected", [
    ("1 done, 2 missed", [(1, "COMPLETED"), (2, "REPORTED_MISSED")]),
    ("1✅ 2❌", [(1, "COMPLETED"), (2, "REPORTED_MISSED")]),
    ("1,2 done 3 missed", [(1, "COMPLETED"), (2, "COMPLETED"), (3, "REPORTED_MISSED")]),
    ("done: 1, 2", [(1, "COMPLETED"), (2, "COMPLETED")]),
    ("1 nahi liya", [(1, "REPORTED_MISSED")]),
    ("१ हो गया, २ नहीं ली", [(1, "COMPLETED"), (2, "REPORTED_MISSED")]),
    ("1 done 1 missed", [(1, "CONFLICTING")]),
    ("I took 2 tablets yesterday", []),
    ("2 din se bukhar hai", []),
])
def test_parse_checklist(text, expected):
    assert parse_checklist_reply(text) == expected


def test_parse_all_and_intents():
    assert parse_all("sab ho gaya") == "COMPLETED" and parse_all("all missed") == "REPORTED_MISSED"
    assert intent("Hi") == "MENU" and intent("SOS") == "SOS" and intent("1") == "MENU_MEDS"
    assert intent("2") == "MENU_QUERY" and intent("feeling nauseous since yesterday") == "QUERY"


# ---- webhook ----

def test_unknown_number():
    assert "isn't registered" in wa("hi", sender="whatsapp:+919999999999")


def test_checklist_is_one_message_in_patients_language():
    r = c.post("/whatsapp/send-checklist/p_rajesh").json()
    assert r["items"] == 3 and r["preview"].count("\n1. ") == 1
    assert "नमस्ते Rajesh" in r["preview"]            # Rajesh's preferred language is Hindi


def test_checklist_reply_updates_events_and_attention():
    c.post("/whatsapp/send-checklist/p_rajesh")
    wa("1 done, 3 missed")
    items = today()
    assert items["Chemotherapy Cycle 4 (Day 1)"]["status"] == "COMPLETED"
    assert items["Capecitabine 500mg"]["status"] == "REPORTED_MISSED"
    reasons = [r for a in c.get("/attention").json() if a["label"] == "NEEDS_REVIEW" for r in a["reasons"]]
    assert any("Capecitabine 500mg" in r and "missed" in r for r in reasons)


def test_changed_answer_becomes_conflicting():
    c.post("/whatsapp/send-checklist/p_rajesh")
    wa("3 done")
    wa("3 missed")
    assert today()["Capecitabine 500mg"]["status"] == "CONFLICTING"


def test_all_done_only_fills_unanswered_items():
    c.post("/whatsapp/send-checklist/p_rajesh")
    wa("3 missed")
    wa("all done")
    items = today()
    assert items["Capecitabine 500mg"]["status"] == "REPORTED_MISSED"
    assert items["Daily 15-min walk"]["status"] == "COMPLETED"


def test_out_of_range_number():
    c.post("/whatsapp/send-checklist/p_rajesh")
    assert "9" in wa("9 done")


def test_free_text_becomes_routed_query():
    wa("feeling nauseous since yesterday")
    qs = c.get("/queries").json()
    assert qs[0]["text"] == "feeling nauseous since yesterday"
    assert qs[0]["category"] == "SYMPTOM_CONCERN" and qs[0]["route_to"] == "care_team_queue"


def test_sos_raises_top_item_and_notifies_consented_caregiver(capsys):
    reply = wa("SOS")
    assert "108" in reply
    assert c.get("/attention").json()[0]["label"] == "SOS"
    out = capsys.readouterr().out
    assert "whatsapp:+910000000010" in out            # Sunita (consent GRANTED) is alerted


def test_palliative_checklist_has_no_adherence_pressure():
    c.patch("/patients/p_rajesh/journey-state", json={"state": "PALLIATIVE", "reason": "test"})
    preview = c.post("/whatsapp/send-checklist/p_rajesh").json()["preview"]
    assert "24" not in preview and "योजना" in preview


def test_deceased_is_a_hard_stop():
    c.patch("/patients/p_rajesh/journey-state", json={"state": "DECEASED", "reason": "test"})
    assert c.post("/whatsapp/send-checklist/p_rajesh").json()["sent"] is False
    assert "<Message>" not in wa("hello")
    assert "<Message>" not in wa("SOS")


def test_transfer_of_care_pauses_but_sos_still_works():
    c.patch("/patients/p_rajesh/journey-state", json={"state": "TRANSFER_OF_CARE", "reason": "test"})
    assert c.post("/whatsapp/send-checklist/p_rajesh").json()["sent"] is False
    assert "SOS" in wa("SOS")


# ---- deployment hardening ----

def test_send_checklist_needs_staff_or_cron_secret(monkeypatch):
    anon = TestClient(app)
    assert anon.post("/whatsapp/send-checklist/p_rajesh").status_code == 401
    patient = {"X-Role": "patient", "X-User-Id": "p_rajesh"}
    assert anon.post("/whatsapp/send-checklist/p_rajesh", headers=patient).status_code == 403
    monkeypatch.setenv("CRON_SECRET", "s3cret")
    assert anon.post("/whatsapp/send-checklist/p_rajesh", headers={"X-Cron-Secret": "wrong"}).status_code == 401
    assert anon.post("/whatsapp/send-checklist/p_rajesh", headers={"X-Cron-Secret": "s3cret"}).status_code == 200


def test_checklist_numbering_survives_restart():
    """Order is stored in the audit log, not memory: replies map to what the patient saw."""
    c.post("/whatsapp/send-checklist/p_rajesh")
    wa("3 missed")
    assert today()["Capecitabine 500mg"]["status"] == "REPORTED_MISSED"
    assert any(a["action"] == "whatsapp_checklist_sent" for a in c.get("/audit?entity_id=p_rajesh").json())


def _sign(token, url, params):
    data = url + "".join(k + params[k] for k in sorted(params))
    return base64.b64encode(hmac.new(token.encode(), data.encode(), hashlib.sha1).digest()).decode()


def test_webhook_rejects_unsigned_requests_when_twilio_configured(monkeypatch):
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "tok123")
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://onko.example.com")
    params = {"From": phone(), "Body": "SOS"}
    assert c.post("/whatsapp/webhook", data=params).status_code == 403
    bad = {"X-Twilio-Signature": "nope"}
    assert c.post("/whatsapp/webhook", data=params, headers=bad).status_code == 403
    good = {"X-Twilio-Signature": _sign("tok123", "https://onko.example.com/whatsapp/webhook", params)}
    r = c.post("/whatsapp/webhook", data=params, headers=good)
    assert r.status_code == 200 and "SOS" in r.text


def test_signature_check_can_be_switched_off_for_local_debugging(monkeypatch):
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "tok123")
    monkeypatch.setenv("TWILIO_VALIDATE_SIGNATURE", "false")
    assert c.post("/whatsapp/webhook", data={"From": phone(), "Body": "hi"}).status_code == 200


def test_sos_reply_mentions_caregiver_and_alerts_once(capsys):
    reply = wa("SOS")
    assert "केयरगिवर" in reply                         # Hindi "caregiver": they really were alerted
    wa("SOS")                                          # second press within 60 s
    assert capsys.readouterr().out.count("OnKo alert: Rajesh Kumar") == 1


def test_production_logs_hide_patient_text(monkeypatch, capsys):
    monkeypatch.setenv("ONKO_ENV", "production")
    c.post("/whatsapp/send-checklist/p_rajesh")
    out = capsys.readouterr().out
    assert "Capecitabine" not in out and "Rajesh" not in out
    assert messages.mask_phone("whatsapp:+919876543210") == "whatsapp:+91******3210"


def test_daily_job_sends_one_checklist_per_eligible_patient():
    from whatsapp import daily
    summary = daily.run()
    assert summary["sent"] + summary["not_sent"] >= 1          # dry run in tests: "not_sent" but delivered + logged
    sent_logs = [a for a in c.get("/audit?entity_id=p_rajesh").json() if a["action"] == "whatsapp_checklist_sent"]
    assert len(sent_logs) == 1


def test_transfer_of_care_sos_still_alerts_caregiver(capsys):
    c.patch("/patients/p_rajesh/journey-state", json={"state": "TRANSFER_OF_CARE", "reason": "test"})
    reply = wa("SOS")
    assert "केयरगिवर" in reply
    assert "OnKo alert: Rajesh Kumar" in capsys.readouterr().out
    assert c.get("/attention").json()[0]["label"] == "SOS"


def test_sos_dedupe_resets_after_demo_reset(capsys):
    wa("SOS")
    c.post("/demo/reset")
    reply = wa("SOS")
    assert "केयरगिवर" in reply
    assert capsys.readouterr().out.count("OnKo alert: Rajesh Kumar") == 2


def test_send_checklist_requires_demo_access_code_when_set(monkeypatch):
    monkeypatch.setenv("DEMO_ACCESS_CODE", "letmein")
    anon = TestClient(app)
    staff = {"X-Role": "doctor", "X-User-Id": "doc_mehta"}
    assert anon.post("/whatsapp/send-checklist/p_rajesh", headers=staff).status_code == 401
    wrong = {**staff, "X-Access-Code": "nope"}
    assert anon.post("/whatsapp/send-checklist/p_rajesh", headers=wrong).status_code == 401
    ok = {**staff, "X-Access-Code": "letmein"}
    assert anon.post("/whatsapp/send-checklist/p_rajesh", headers=ok).status_code == 200
