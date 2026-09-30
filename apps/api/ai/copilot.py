"""AI #3 — Care Plan Copilot. Structures what the doctor wrote. Invents nothing.

Pipeline:
  doctor text --> LLM (if configured) --> validate + ground every item --> normalise schedules --> draft
             \-> rule-based structurer (if LLM unavailable / invalid)  -^
Either way the result is only a DRAFT; core stores it and the doctor must approve.
"""
import re
from datetime import date, timedelta
from ai.client import call_json, load_prompt, today_ist
from ai.dates import find_date, valid_iso
from ai.guardrails import items_grounded_in_source, ungrounded_terms

TYPES = {"MEDICATION", "INVESTIGATION", "TREATMENT", "APPOINTMENT", "MILESTONE"}
FALLBACK = {"ok": False, "items": [], "unparsed_text": "", "warnings": ["AI unavailable — enter items manually"]}

# Frequency shorthand -> (plain words, default reminder times). Times are reminder slots, not clinical advice;
# the doctor can edit them in the draft.
FREQ = [
    (r"\b(qid|four times (a|per) day)\b", "four times daily", "daily 08:00, 12:00, 16:00, 20:00"),
    (r"\b(tds|tid|thrice daily|three times (a|per) day)\b", "three times daily", "daily 08:00, 14:00, 20:00"),
    (r"\b(bd|bid|twice daily|twice a day|two times (a|per) day)\b", "twice daily", "daily 09:00, 21:00"),
    (r"\b(hs|at bedtime|at night)\b", "at bedtime", "daily 21:00"),
    (r"\b(od|once daily|once a day|daily)\b", "once daily", "daily 09:00"),
    (r"\b(weekly|once a week)\b", "weekly", "weekly"),
]
TIMING = r"\b(after food|before food|with food|after meals?|before meals?|empty stomach|before chemo\w*|after chemo\w*|" \
         r"before breakfast|after breakfast|before dinner|after dinner)\b"
DOSE = r"\b(\d+(?:\.\d+)?\s*(?:mg|mcg|µg|g|ml|iu|units?)(?:/(?:m2|kg))?)\b"
DURATION = r"\b(?:for|x|×)\s*(\d+)\s*(days?|weeks?)\b"

KEYWORDS = {
    "TREATMENT": r"\b(chemo\w*|cycle|radiation|radiotherapy|rt|surgery|infusion|immunotherapy|transfusion|"
                 r"procedure|fraction\w*|port flush)\b",
    "INVESTIGATION": r"\b(cbc|lft|kft|rft|test|tests|scan|ct|mri|pet|pet-ct|x-?ray|ultrasound|usg|biopsy|blood work|"
                     r"echo|ecg|tumou?r markers?|cea|ca-?125|psa|urine|labs?)\b",
    "APPOINTMENT": r"\b(review|follow[- ]?up|consult\w*|teleconsult\w*|appointment|visit|opd)\b",
    "MILESTONE": r"\b(walk\w*|exercise|diet|water|steps|milestone|yoga|breathing|mouthwash|weigh\w*)\b",
}
MED_CUES = DOSE + r"|\b(tab|tablet|tablets|cap|capsule|inj|injection|syrup|od|bd|bid|tds|tid|qid|hs)\b"
LEAD_VERBS = {"start", "continue", "give", "take", "tab", "tablet", "cap", "capsule", "inj", "injection", "syrup"}
NOT_A_DRUG = {"patient", "pt", "please", "cycle", "review", "plan", "next", "then", "also", "and", "the", "on"}
STOP_WORDS = r"\b(stop|discontinue|hold|withhold|omit)\b"


def _sentences(text: str) -> list[str]:
    text = re.sub(r"\b(Dr|Mr|Mrs|Ms|Tab|Inj|Cap|No|Approx)\.", r"\1", text or "", flags=re.I)  # not sentence ends
    parts = re.split(r"(?<=[.;])\s+|\n+|;", text)
    return [p.strip(" .;\t") for p in parts if p and p.strip(" .;\t")]


def _classify(frag: str) -> str | None:
    t = frag.lower()
    words = re.findall(r"[a-z][a-z0-9-]*", t)
    while words and words[0] in LEAD_VERBS:
        words = words[1:]
    first = words[0] if words else ""
    looks_like_drug = (len(first) >= 4 and first not in NOT_A_DRUG
                       and not any(re.fullmatch(k, first) for k in KEYWORDS.values()))
    if re.search(MED_CUES, t) or (looks_like_drug and (re.search(TIMING, t) or re.search(DURATION, t))):
        return "MEDICATION"
    hits = [(m.start(), cat) for cat, rx in KEYWORDS.items() for m in [re.search(rx, t)] if m]
    if hits:
        return min(hits)[1]
    if looks_like_drug and re.search(r"\b(before|after|with)\b", t):
        return "MEDICATION"      # "Ondansetron before chemo"
    return None


def _clean_title(frag: str, date_text: str | None) -> str:
    t = frag
    if date_text:
        t = t.replace(date_text, " ")
    t = re.sub(r"\b(on|by|from|at|dated)\s*$", "", t.strip(), flags=re.I)
    t = re.sub(r"\b(on|by|from|dated)\s+(?=\W*$)", "", t, flags=re.I)
    t = re.sub(r"\s{2,}", " ", t).strip(" ,.-")
    return t[:1].upper() + t[1:] if t else t


def _med_details(frag: str) -> tuple[str, dict]:
    t = frag.lower()
    words = re.findall(r"[A-Za-z][A-Za-z0-9-]*", frag)
    while words and words[0].lower() in LEAD_VERBS:
        words = words[1:]
    name = words[0] if words else frag
    name = name[:1].upper() + name[1:]
    details = {"instructions": frag}
    dose = re.search(DOSE, t)
    if dose:
        details["dose"] = dose.group(1)
    for rx, words_, _ in FREQ:
        if re.search(rx, t):
            details["frequency"] = words_
            break
    timing = re.search(TIMING, t)
    if timing:
        details["timing"] = timing.group(1)
    dur = re.search(DURATION, t)
    if dur:
        details["duration"] = f"{dur.group(1)} {dur.group(2)}"
    title = f"{name} {dose.group(1).replace(' ', '')}" if dose else name
    return title, details


def _treatment_title(frag: str, date_text: str | None) -> str:
    t = frag.lower()
    cyc = re.search(r"\bcycle\s*(\d+)", t) or re.search(r"\bc(\d+)\b", t)
    if re.search(r"\bchemo", t) and cyc:
        day = re.search(r"\bday\s*(\d+)", t)
        return f"Chemotherapy Cycle {cyc.group(1)}" + (f" (Day {day.group(1)})" if day else "")
    return _clean_title(frag, date_text)


def recurrence_for(item: dict) -> str | None:
    text = f"{item.get('source_span', '')} {(item.get('details') or {}).get('frequency', '')}".lower()
    for rx, _, rec in FREQ:
        if re.search(rx, text):
            return rec
    return None


def end_date_for(item: dict) -> str | None:
    """'for 14 days' + start 2026-10-15 -> 2026-10-28 (inclusive). Arithmetic on what the doctor wrote."""
    start = item.get("start_date")
    dur = re.search(DURATION, (item.get("source_span") or "").lower())
    if not (start and valid_iso(start) and dur):
        return None
    n = int(dur.group(1)) * (7 if dur.group(2).startswith("week") else 1)
    return (date.fromisoformat(start) + timedelta(days=n - 1)).isoformat()


def rule_based_structure(raw_text: str) -> dict:
    """No-LLM structurer. Deterministic, only ever copies from the doctor's text."""
    items, unparsed, warnings = [], [], []
    for frag in _sentences(raw_text):
        if re.search(STOP_WORDS, frag.lower()):
            unparsed.append(frag)
            warnings.append(f"'{frag}' looks like a stop/hold instruction — update the care plan manually.")
            continue
        kind = _classify(frag)
        if not kind:
            unparsed.append(frag)
            continue
        iso, date_text = find_date(frag, prefer="future")
        details: dict = {"instructions": frag}
        if kind == "MEDICATION":
            title, details = _med_details(frag)
        elif kind == "TREATMENT":
            title = _treatment_title(frag, date_text)
        else:
            title = _clean_title(frag, date_text)
        items.append({"type": kind, "title": title or frag, "details": details, "start_date": iso or "",
                      "end_date": None, "recurrence": None, "source_span": frag})
    return {"items": items, "unparsed_text": ". ".join(unparsed), "warnings": warnings}


def _finalise(out: dict, raw_text: str) -> dict:
    """Validate + ground + normalise. Applied to BOTH the LLM output and the rule-based output."""
    warnings = [w for w in out.get("warnings", []) if isinstance(w, str)]
    clean = []
    for it in out.get("items", []):
        if not isinstance(it, dict) or not it.get("title"):
            continue
        it = {
            "type": str(it.get("type", "")).upper(),
            "title": str(it["title"]).strip(),
            "details": it.get("details") if isinstance(it.get("details"), dict) else {},
            "start_date": it.get("start_date") or "",
            "end_date": it.get("end_date") or None,
            "recurrence": it.get("recurrence") or None,
            "source_span": it.get("source_span") or "",
        }
        if it["type"] not in TYPES:
            warnings.append(f"'{it['title']}': unknown type '{it['type']}' — set to MILESTONE, please check.")
            it["type"] = "MILESTONE"
        # dates must be real ISO dates
        if it["start_date"] and not valid_iso(it["start_date"]):
            it["start_date"] = ""
        if it["end_date"] and not valid_iso(it["end_date"]):
            it["end_date"] = None
        if it["type"] == "MILESTONE" and not it["recurrence"]:
            it["recurrence"] = {"once daily": "daily", "weekly": "weekly"}.get(
                (recurrence_for(it) or "").replace("daily 09:00", "once daily"))
        if it["type"] == "MEDICATION":
            it["recurrence"] = it["recurrence"] or recurrence_for(it)
            it["end_date"] = it["end_date"] or end_date_for(it)
            dose = str(it["details"].get("dose", ""))
            if dose and ungrounded_terms(dose, raw_text):
                warnings.append(f"Dose '{dose}' for {it['title']} not found in your text — removed.")
                it["details"].pop("dose")
            if not it["details"].get("dose"):
                warnings.append(f"Dose not specified for {it['title']} — left blank for doctor.")
        if not it["start_date"]:
            warnings.append(f"No date given for {it['title']} — set it before approving.")
        elif it["end_date"] and it["end_date"] < it["start_date"]:
            warnings.append(f"{it['title']}: end date is before start date — please check.")
        clean.append(it)

    if out.get("unparsed_text"):
        warnings.append(f"Not structured (please add manually if needed): '{out['unparsed_text']}'")
    invented = set(items_grounded_in_source(clean, raw_text))
    if invented:
        clean = [i for i in clean if i["title"] not in invented]
        warnings.append(f"Removed items not found in doctor's text: {sorted(invented)}")
    return {"items": clean, "unparsed_text": out.get("unparsed_text") or "", "warnings": warnings}


def structure_care_plan(raw_text: str, patient_ctx: dict) -> dict:
    """(raw_text, patient_ctx) -> CopilotOutput. Never raises."""
    try:
        today = today_ist()
        user = (f"Today is {today:%A, %d %B %Y} ({today.date().isoformat()}). "
                f"Dates without a year mean the next occurrence on or after today.\n\n"
                f"Doctor's plan:\n{raw_text}")
        out = call_json(load_prompt("copilot"), user)
        if out and isinstance(out.get("items"), list):
            result = _finalise(out, raw_text)
            return {"ok": True, **result}
        # LLM unavailable or gave junk -> deterministic structurer, clearly labelled
        result = _finalise(rule_based_structure(raw_text), raw_text)
        result["warnings"].insert(0, "AI unavailable — structured with basic rules. Please check every item.")
        return {"ok": False, **result}
    except Exception as e:  # noqa: BLE001  (never crash the route)
        print(f"[ai.copilot] error: {e}")
        return {**FALLBACK, "unparsed_text": raw_text}
