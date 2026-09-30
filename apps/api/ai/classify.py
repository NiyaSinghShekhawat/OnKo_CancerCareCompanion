"""Query classification + factual summary + routing. No advice. No severity."""
from ai.client import call_json, load_prompt
from ai.guardrails import has_clinical_language

ROUTE = {"ADMINISTRATIVE": "admin_queue", "MEDICATION": "care_team_queue", "SYMPTOM_CONCERN": "care_team_queue"}
MED_WORDS = ["tablet", "medicine", "dose", "capecitabine", "pill", "injection", "dawai"]
SYMPTOM_WORDS = ["pain", "nause", "vomit", "fever", "tired", "bleed", "swell", "dizzy", "breath", "rash", "ulti"]


def _keyword_fallback(text: str) -> dict:
    t = text.lower()
    cat = ("MEDICATION" if any(w in t for w in MED_WORDS)
           else "SYMPTOM_CONCERN" if any(w in t for w in SYMPTOM_WORDS) else "ADMINISTRATIVE")
    return {"ok": True, "category": cat, "summary": f"Patient message: {text[:140]}", "route_to": ROUTE[cat]}


def classify_query(text: str) -> dict:
    out = call_json(load_prompt("classify"), text)
    if not out or out.get("category") not in ROUTE or has_clinical_language(out.get("summary", "")):
        return _keyword_fallback(text)
    out["route_to"] = ROUTE[out["category"]]
    out["ok"] = True
    return out
