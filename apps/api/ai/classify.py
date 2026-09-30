"""Query classification + factual summary + routing. No advice. No severity. No emergency inference."""
import re
from ai.client import call_json, load_prompt
from ai.guardrails import has_clinical_language

ROUTE = {"ADMINISTRATIVE": "admin_queue", "MEDICATION": "care_team_queue", "SYMPTOM_CONCERN": "care_team_queue"}

# Whole-word / word-start matches. English + common Hindi / Hinglish / Telugu (romanised) words.
MED_WORDS = [
    r"tablets?", r"medicines?", r"medications?", r"dose", r"doses", r"capecitabine", r"pills?", r"injections?",
    r"capsules?", r"syrup", r"prescription", r"refill",
    r"dawai", r"dawaai", r"dava", r"dawa", r"goli", r"goliyan", r"mandu", r"mandulu", r"billa",
]
SYMPTOM_WORDS = [
    r"pain\w*", r"ache\w*", r"hurt\w*", r"nause\w*", r"vomit\w*", r"fever\w*", r"tired\w*", r"fatigue\w*",
    r"weak\w*", r"bleed\w*", r"blood", r"swell\w*", r"swollen", r"dizz\w*", r"breath\w*", r"rash\w*",
    r"itch\w*", r"diarrh\w*", r"loose motion\w*", r"constipat\w*", r"cough\w*", r"sore\w*", r"ulcer\w*",
    r"numb\w*", r"tingl\w*", r"burn\w*", r"appetite", r"sleep\w*", r"headache\w*", r"chills?", r"faint\w*",
    r"discomfort", r"unwell", r"sick", r"cramp\w*", r"mouth sores?",
    # Hindi / Hinglish
    r"dard", r"bukhar", r"bukhaar", r"ulti", r"ultee", r"chakkar", r"kamzori", r"kamjori", r"khoon",
    r"saans", r"sujan", r"soojan", r"jalan", r"dast", r"khansi", r"thakan", r"thakaan", r"ji machal\w*",
    r"bhook", r"neend",
    # Telugu
    r"noppi", r"jwaram", r"vanthi", r"vaanti", r"neerasam", r"kallu tirugu\w*",
]
_MED_RE = re.compile(r"\b(" + "|".join(MED_WORDS) + r")\b", re.I)
_SYM_RE = re.compile(r"\b(" + "|".join(SYMPTOM_WORDS) + r")\b", re.I)


def _keyword_category(text: str) -> str:
    if _MED_RE.search(text or ""):
        return "MEDICATION"
    if _SYM_RE.search(text or ""):
        return "SYMPTOM_CONCERN"
    return "ADMINISTRATIVE"


def _keyword_fallback(text: str) -> dict:
    cat = _keyword_category(text)
    clipped = re.sub(r"\s+", " ", (text or "").strip())
    clipped = clipped if len(clipped) <= 140 else clipped[:137] + "..."
    # The patient's own words, quoted — not an AI interpretation.
    return {"ok": True, "category": cat, "summary": f'Patient message: "{clipped}"', "route_to": ROUTE[cat]}


def _summary_ok(summary) -> bool:
    return (isinstance(summary, str) and 0 < len(summary.strip()) <= 400
            and not has_clinical_language(summary))


def classify_query(text: str) -> dict:
    """(text) -> QueryClassification. Never raises."""
    try:
        out = call_json(load_prompt("classify"), text)
        if not out or out.get("category") not in ROUTE or not _summary_ok(out.get("summary")):
            return _keyword_fallback(text)
        # Safety net: if the patient mentioned a medicine or symptom, never let it land in the admin queue.
        cat = out["category"]
        kw = _keyword_category(text)
        if cat == "ADMINISTRATIVE" and kw != "ADMINISTRATIVE":
            cat = kw
        return {"ok": True, "category": cat, "summary": out["summary"].strip(), "route_to": ROUTE[cat]}
    except Exception as e:  # noqa: BLE001
        print(f"[ai.classify] error: {e}")
        return _keyword_fallback(text)
