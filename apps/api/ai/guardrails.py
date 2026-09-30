"""Output checks. If something clinical slips through, we reject it."""
import re

BANNED = [
    r"\banemi[ac]\b", r"\babnormal\b", r"\bworsening\b", r"\bimproving\b", r"\bhigh[- ]risk\b",
    r"\bdiagnos", r"\bprognosis\b", r"\byou should (take|stop|start)\b", r"\bincrease the dose\b",
    r"\bemergency\b", r"\bsevere\b", r"\bcritical\b", r"\blow (hb|haemoglobin|hemoglobin)\b",
]


def has_clinical_language(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in BANNED)


def items_grounded_in_source(items: list[dict], source: str) -> list[str]:
    """Return titles of items whose name doesn't appear in the doctor's text (invented = rejected)."""
    src = source.lower()
    return [it.get("title", "") for it in items
            if it.get("title") and it["title"].split()[0].lower() not in src]
