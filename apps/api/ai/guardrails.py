"""Output checks. If something clinical slips through, we reject it.

Two kinds of check:
  1. has_clinical_language()  - AI text must not interpret, judge, advise or escalate.
  2. grounding checks         - AI output must not contain anything the doctor / report didn't say.
"""
import re

# Interpretation, judgement, advice, severity, causation. Whole-word patterns.
BANNED = [
    # lab interpretation
    r"\banemi[ac]\b", r"\banaemi[ac]\b", r"\babnormal(ly)?\b", r"\bnormal\b",
    r"\b(low|high|elevated|raised|reduced|decreased|increased|deranged)\s+(hb|haemoglobin|hemoglobin|wbc|"
    r"platelets?|counts?|values?|levels?|sugar|creatinine|bilirubin)\b",
    r"\b(within|outside|out of|below|above)\s+(the\s+)?(normal|reference)\b",
    r"\bneutropeni[ac]\b", r"\bthrombocytopeni[ac]\b",
    # trend / status judgement
    r"\bworsen(ing|ed)?\b", r"\bimprov(ing|ed|ement)\b", r"\bdeteriorat", r"\bprogress(ion|ing)\b",
    r"\bstable\b", r"\bconcerning\b", r"\balarming\b", r"\bworrying\b",
    # risk / diagnosis / prognosis
    r"\bhigh[- ]risk\b", r"\brisk\b", r"\bdiagnos", r"\bprognos", r"\blikely\b", r"\bsuggest(s|ive)\b",
    r"\bindicat(es|ive|ing)\b", r"\bconsistent with\b",
    # causation
    r"\bside[- ]effects?\b", r"\bcaused by\b", r"\bdue to (the )?(chemo|treatment|medication|medicine|drug)",
    # advice
    r"\byou should\b", r"\bshould (take|stop|start|skip|continue|increase|reduce)\b",
    r"\b(increase|reduce|decrease|double|halve) the dose\b", r"\brecommend", r"\badvis(e|ed)\b",
    r"\bgo to (the )?(hospital|er|emergency)\b",
    # severity / emergency (SOS is patient-triggered only)
    r"\bemergency\b", r"\bsevere(ly)?\b", r"\bcritical(ly)?\b", r"\burgent(ly)?\b", r"\blife[- ]threatening\b",
]
_BANNED_RE = [re.compile(p) for p in BANNED]


def has_clinical_language(text: str) -> bool:
    t = (text or "").lower()
    return any(p.search(t) for p in _BANNED_RE)


# ---------- grounding ----------

def norm(s: str) -> str:
    """lowercase, unify dashes/spaces so '500 mg' and '500mg' compare sensibly."""
    s = (s or "").lower().replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", s).strip()


def _squash(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", norm(s))


# Words the Copilot may use in a title even if the doctor abbreviated them.
GENERIC_WORDS = {
    "chemotherapy", "chemo", "cycle", "day", "review", "appointment", "follow", "followup", "up",
    "consultation", "consult", "teleconsult", "visit", "test", "tablet", "tablets", "tab", "capsule",
    "injection", "inj", "dose", "daily", "twice", "once", "before", "after", "food", "oral", "start",
    "end", "milestone", "treatment", "investigation", "medication", "with", "doctor", "dr", "and", "the",
    "of", "for", "on", "at", "in", "session", "infusion", "blood", "report", "scan", "morning", "evening",
    "night", "weekly", "radiation", "radiotherapy", "fraction", "surgery", "procedure", "check", "reminder",
}


def _word_grounded(word: str, src_words: set[str], src_squashed: str) -> bool:
    if word in GENERIC_WORDS or word in src_words:
        return True
    if len(word) >= 5 and any(w.startswith(word[:5]) for w in src_words):   # "chemotherapy" ~ "chemo" handled above
        return True
    return word in src_squashed


def ungrounded_terms(text: str, source: str) -> list[str]:
    """Words / numbers in `text` that don't appear in `source` (ignoring generic workflow words)."""
    src = norm(source)
    src_words = set(re.findall(r"[a-z]+", src))
    src_nums = set(re.findall(r"\d+(?:\.\d+)?", src))
    src_squashed = _squash(source)
    bad = []
    for w in re.findall(r"[a-z]+", norm(text)):
        if len(w) >= 3 and not _word_grounded(w, src_words, src_squashed):
            bad.append(w)
    for n in re.findall(r"\d+(?:\.\d+)?", norm(text)):
        if n not in src_nums:
            bad.append(n)
    return bad


def items_grounded_in_source(items: list[dict], source: str) -> list[str]:
    """Return titles of items that contain a name / number the doctor never wrote (invented = rejected).

    An item is grounded when:
      - its source_span (if given) really is a fragment of the doctor's text, and
      - every non-generic word and every number in its title appears in the doctor's text.
    """
    src_squashed = _squash(source)
    invented = []
    for it in items:
        title = it.get("title") or ""
        span = it.get("source_span") or ""
        if span and _squash(span) not in src_squashed:
            invented.append(title)
        elif ungrounded_terms(title, source):
            invented.append(title)
    return invented
