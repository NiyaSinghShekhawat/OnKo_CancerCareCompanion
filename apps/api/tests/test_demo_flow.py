"""docs/DEMO_FLOW.md, end to end through the API (owner: Samprada).

One seeded throwaway database (test_onko.db, via conftest.py) for the whole file; AI and Twilio keys are
blanked, so the Copilot / classifier / extractor use their rule-based fallbacks and WhatsApp runs in dry-run
mode. The steps share state and run in file order — run the file as a whole, not single steps."""
import re
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from ai.guardrails import has_clinical_language
from core import seed
from core.timeutil import utcnow
from main import app

c = TestClient(app)   # no default headers: every call says who is acting
DOCTOR = {"X-Role": "doctor", "X-User-Id": "doc_mehta"}
RAJESH = {"X-Role": "patient", "X-User-Id": "p_rajesh"}
SUNITA = {"X-Role": "caregiver", "X-User-Id": "cg_sunita"}
DEMO_TEXT = ("Cycle 5 chemo on 15 Oct. Capecitabine 500mg BD after food for 14 days. "
             "Ondansetron before chemo. CBC on 13 Oct. Review on 16 Oct.")
INTERPRETATION = re.compile(r"\b(risk|high-risk|severe|critical|worsening|improving|concerning|abnormal|"
                            r"anaemi\w*|anemi\w*|low|high|prognos\w*|deteriorat\w*)\b", re.IGNORECASE)
ATTENTION_ITEM_KEYS = {"id", "patient_id", "patient_name", "label", "reasons", "status", "assigned_to", "created_at"}
EXTRACTED_VALUE_KEYS = {"name", "value", "unit", "reference_range_as_printed", "source_line"}
state = {}


@pytest.fixture(scope="module", autouse=True)
def seeded_once():
    seed.run()   # WhatsApp keeps its SOS de-dupe / last-checklist state in the DB, so a reseed resets it too


def factual(text: str) -> bool:
    return not has_clinical_language(text) and not INTERPRETATION.search(text)


def rajesh_items(label=None):
    items = c.get("/attention?patient_id=p_rajesh", headers=DOCTOR).json()
    return [a for a in items if label is None or a["label"] == label]


def reasons(label):
    return [r for a in rajesh_items(label) for r in a["reasons"]]


def timeline():
    return c.get("/patients/p_rajesh/timeline", headers=DOCTOR).json()


def day(d) -> str:
    return f"{d:%d %b}"


# ---------- 1-2. Care Plan Copilot: draft → approve blocked → doctor sets dates → approve ----------

def test_01_copilot_drafts_structured_items_from_the_demo_text():
    state["events_before"] = len(timeline())
    r = c.post("/careplan/draft", json={"patient_id": "p_rajesh", "raw_text": DEMO_TEXT}, headers=DOCTOR)
    assert r.status_code == 200
    draft = r.json()
    assert draft["status"] == "DRAFT" and draft["ok"] is False                       # AI blanked → basic rules
    assert any("AI unavailable" in w for w in draft["warnings"])
    by_title = {it["title"]: it for it in draft["items"]}
    assert {t: by_title[t]["type"] for t in by_title} == {
        "Chemotherapy Cycle 5": "TREATMENT", "Capecitabine 500mg": "MEDICATION", "Ondansetron": "MEDICATION",
        "CBC": "INVESTIGATION", "Review": "APPOINTMENT"}
    assert by_title["Capecitabine 500mg"]["recurrence"] == "daily 09:00, 21:00"
    assert by_title["Capecitabine 500mg"]["start_date"] == "" and by_title["Ondansetron"]["start_date"] == ""
    assert len(timeline()) == state["events_before"]                                  # a draft creates nothing
    state["draft"] = draft


def test_02_approve_is_blocked_until_every_item_has_a_start_date():
    draft = state["draft"]
    r = c.post(f"/careplan/draft/{draft['id']}/approve", headers=DOCTOR)
    assert r.status_code == 400 and r.json()["detail"] == "Set a start date for: Capecitabine 500mg, Ondansetron"
    assert len(timeline()) == state["events_before"]
    assert c.get("/patients/p_rajesh/careplan", headers=DOCTOR).json() == []


def test_03_doctor_sets_the_missing_dates():
    draft = state["draft"]
    today = utcnow().date()
    chemo_day = next(it["start_date"] for it in draft["items"] if it["title"] == "Chemotherapy Cycle 5")
    items = []
    for it in draft["items"]:
        if it["title"] == "Capecitabine 500mg":
            it = {**it, "start_date": today.isoformat()}          # starts today, so tonight's dose is on today's checklist
        elif it["title"] == "Ondansetron":
            it = {**it, "start_date": chemo_day}                  # "before chemo"
        items.append(it)
    r = c.put(f"/careplan/draft/{draft['id']}", json={"items": items}, headers=DOCTOR)
    assert r.status_code == 200 and r.json()["status"] == "DRAFT"
    state["today"] = today


def test_04_approve_puts_the_events_on_the_timeline():
    r = c.post(f"/careplan/draft/{state['draft']['id']}/approve", headers=DOCTOR)
    assert r.status_code == 200
    created = r.json()
    counts = {}
    for e in created:
        counts[e["title"]] = counts.get(e["title"], 0) + 1
        assert e["source"] == "copilot_approved" and e["journey_chapter"] == 1 and e["status"] == "UPCOMING"
    assert counts == {"Chemotherapy Cycle 5": 1, "Capecitabine 500mg": 28,           # 14 days × 09:00 + 21:00
                      "Ondansetron": 1, "CBC": 1, "Review": 1}
    tl = timeline()
    assert len(tl) == state["events_before"] + 32
    assert [e["scheduled_at"] for e in tl] == sorted(e["scheduled_at"] for e in tl)
    cape = next(i for i in c.get("/patients/p_rajesh/careplan", headers=DOCTOR).json() if i["title"] == "Capecitabine 500mg")
    assert cape["end_date"] == (state["today"] + timedelta(days=13)).isoformat()      # "for 14 days", inclusive


# ---------- 3-4. Today's checklist → patient reports the evening Capecitabine as missed ----------

def test_05_patient_reports_tonights_capecitabine_missed():
    items = c.get("/patients/p_rajesh/checklist/today", headers=RAJESH).json()["items"]
    tonight = [e for e in items if e["title"] == "Capecitabine 500mg" and e["scheduled_at"].endswith("T21:00:00")
               and e["source"] == "copilot_approved"]
    assert len(tonight) == 1
    r = c.patch(f"/events/{tonight[0]['id']}/status", json={"status": "REPORTED_MISSED", "source": "patient"},
                headers=RAJESH)
    assert r.status_code == 200 and r.json()["status"] == "REPORTED_MISSED"
    assert f"Medication reported missed: Capecitabine 500mg, {day(state['today'])}" in reasons("NEEDS_REVIEW")


# ---------- 5. Symptom query → classified, summarized, routed ----------

def test_06_symptom_query_is_classified_and_routed():
    r = c.post("/queries", json={"patient_id": "p_rajesh", "text": "feeling nauseous since yesterday",
                                 "channel": "whatsapp"}, headers=RAJESH)
    assert r.status_code == 200
    q = r.json()
    assert (q["category"], q["route_to"], q["status"]) == ("SYMPTOM_CONCERN", "care_team_queue", "OPEN")
    assert "nauseous since yesterday" in q["summary"]
    assert f"New patient concern logged: {q['summary']}" in reasons("QUERY")


# ---------- 6. Explainable attention queue: Rajesh, factual reasons only ----------

def test_07_attention_queue_shows_rajesh_with_factual_reasons():
    items = rajesh_items()
    assert {a["label"] for a in items} == {"NEEDS_REVIEW", "QUERY"}
    for a in items:
        assert set(a) == ATTENTION_ITEM_KEYS                     # no score, no risk level, no extra fields
        assert a["patient_name"] == "Rajesh Kumar"
        for reason in a["reasons"]:
            assert factual(reason), reason
    assert any(r.startswith("New report awaiting review: CBC") for r in reasons("NEEDS_REVIEW"))


# ---------- 7. Patient 360: since last review + CBC as extracted values only ----------

def test_08_patient_360_since_last_review_is_factual():
    r = c.get("/patients/p_rajesh/360", headers=DOCTOR)
    assert r.status_code == 200
    summary = r.json()["since_last_review"]
    assert summary["ok"] is True and summary["bullets"]
    assert any(b.startswith("Reported missed: Capecitabine 500mg") for b in summary["bullets"])
    assert any(b.startswith("New query (symptom concern)") for b in summary["bullets"])
    assert any(b.startswith("Hb: 9.2") and "CBC" in b for b in summary["bullets"])     # value as printed
    for line in summary["bullets"] + summary["upcoming"]:
        assert factual(line), line


def test_09_report_is_shown_as_extracted_values_only():
    (report,) = c.get("/patients/p_rajesh/reports", headers=DOCTOR).json()
    assert report["title"] == "CBC — 20 Sep" and report["reviewed"] is False
    hb = next(v for v in report["extracted_values"] if v["name"] == "Hb")
    assert set(hb) == EXTRACTED_VALUE_KEYS                       # no flag, status or interpretation field
    assert (hb["value"], hb["unit"], hb["reference_range_as_printed"]) == ("9.2", "g/dL", "12-15")
    assert f"{hb['name']}: {hb['value']} — {report['title'].replace(' — ', ', ')}" == "Hb: 9.2 — CBC, 20 Sep"

    # a caregiver uploads the same CBC: values are extracted, printed as-is, and queued for review
    r = c.post("/patients/p_rajesh/reports", headers=SUNITA, json={
        "title": "CBC — repeat", "uploaded_by_role": "caregiver",
        "text": "Haemoglobin 9.2 g/dL (12-15)\nWBC 4.1 x10^9/L (4-11)\nPlatelets 180 x10^9/L (150-400)"})
    assert r.status_code == 200
    values = r.json()["extracted_values"]
    assert [(v["name"], v["value"]) for v in values] == [("Hb", "9.2"), ("WBC", "4.1"), ("Platelets", "180")]
    assert all(set(v) == EXTRACTED_VALUE_KEYS for v in values)
    assert "New report awaiting review: CBC — repeat" in reasons("NEEDS_REVIEW")


# ---------- 8. App SOS → caregiver alerted (dry run), SOS on top of the queue ----------

def test_10_app_sos_alerts_the_caregiver_and_tops_the_queue(capsys):
    capsys.readouterr()
    r = c.post("/sos", json={"patient_id": "p_rajesh", "channel": "app"}, headers=RAJESH)
    assert r.status_code == 200
    assert r.json()["label"] == "SOS" and r.json()["reasons"] == ["Patient-triggered SOS via app"]
    out = capsys.readouterr().out
    assert "[whatsapp:dry-run] -> whatsapp:+910000000010" in out                     # Sunita, consent GRANTED
    assert "Rajesh Kumar pressed SOS via app" in out
    assert "+910000000011" not in out                                                # Karthik (Priya's, PENDING)
    top = c.get("/attention", headers=DOCTOR).json()[0]
    assert (top["label"], top["patient_id"], top["status"]) == ("SOS", "p_rajesh", "PENDING")


# ---------- 9. Palliative: no adherence pressure. Deceased: hard stop ----------

def test_11_palliative_drops_adherence_items_and_softens_the_checklist():
    c.patch("/patients/p_rajesh/journey-state", json={"state": "PALLIATIVE", "reason": "demo"}, headers=DOCTOR)
    needs_review = reasons("NEEDS_REVIEW")
    assert needs_review and not any(r.startswith("Medication reported missed") for r in needs_review)
    assert all(r.startswith("New report awaiting review") for r in needs_review)
    assert reasons("SOS") == ["Patient-triggered SOS via app"]                       # SOS stays

    items = c.get("/patients/p_rajesh/checklist/today", headers=RAJESH).json()["items"]
    dose = next(e for e in items if e["title"] == "Capecitabine 500mg" and e["scheduled_at"].endswith("T09:00:00")
                and e["source"] == "copilot_approved")
    c.patch(f"/events/{dose['id']}/status", json={"status": "REPORTED_MISSED"}, headers=RAJESH)
    assert not any(r.startswith("Medication reported missed") for r in reasons("NEEDS_REVIEW"))

    preview = c.post("/whatsapp/send-checklist/p_rajesh", headers=DOCTOR).json()["preview"]
    assert "24" not in preview and "योजना" in preview                               # gentle Hindi wording, no 24h push


def test_12_deceased_closes_everything_and_hard_stops():
    c.patch("/patients/p_rajesh/journey-state", json={"state": "DECEASED", "reason": "demo"}, headers=DOCTOR)
    assert rajesh_items() == []
    out = c.get("/patients/p_rajesh/checklist/today", headers=DOCTOR).json()
    assert out["items"] == [] and out["paused"] is True and out["reason"] == "Journey state DECEASED"
    r = c.post("/sos", json={"patient_id": "p_rajesh", "channel": "app"}, headers=RAJESH)
    assert r.status_code == 409
    phone = c.get("/patients/p_rajesh", headers=DOCTOR).json()["phone_whatsapp"]
    assert "<Message>" not in c.post("/whatsapp/webhook", data={"From": phone, "Body": "SOS"}).text
    assert c.post("/whatsapp/send-checklist/p_rajesh", headers=DOCTOR).json()["sent"] is False
    assert rajesh_items() == []                                                      # nothing new was raised
