"""Report extraction — values exactly as printed. No interpretation.

Every returned value must be traceable: its source_line must be a real line of the report, and its
name / value / unit / reference range must all appear in that line. Anything else is dropped.
Flags such as H / L / * / "High" are never copied.
"""
import re
from ai.client import call_json, load_prompt
from ai.dates import find_date, valid_iso
from ai.guardrails import norm

FALLBACK = {"ok": False, "report_type": "", "report_date": "", "values": []}
ALLOWED_KEYS = ("name", "value", "unit", "reference_range_as_printed", "source_line")

REPORT_TYPES = [
    (r"\b(cbc|complete blood count|haemogram|hemogram)\b", "CBC"),
    (r"\b(lft|liver function)\b", "LFT"), (r"\b(kft|rft|renal function|kidney function)\b", "KFT"),
    (r"\b(pet[- ]?ct)\b", "PET-CT"), (r"\b(ct scan|cect|\bct\b)", "CT"), (r"\bmri\b", "MRI"),
    (r"\b(tumou?r markers?|cea|ca[- ]?125|ca[- ]?19[- ]?9|psa)\b", "Tumour markers"),
    (r"\b(electrolytes|serum sodium)\b", "Electrolytes"), (r"\b(thyroid|tsh)\b", "Thyroid profile"),
]
# Common short names so "Haemoglobin" shows as "Hb" like the spec example. Display-only renaming.
SHORT_NAMES = {"haemoglobin": "Hb", "hemoglobin": "Hb", "white blood cells": "WBC", "total leucocyte count": "TLC",
               "platelet count": "Platelets"}

# "<name> [:|-] <number> [unit] [(range)]"
LINE_RE = re.compile(
    r"^\s*(?P<name>[A-Za-z][A-Za-z0-9 .()/%-]*?[A-Za-z)])\s*[:=\-]?\s+"
    r"(?P<value>\d+(?:\.\d+)?)\s*"
    r"(?P<unit>(?:x\s?10\^?\d+/?[A-Za-zµ]*)|(?:[A-Za-zµ%/][A-Za-z0-9µ%/^.]*))?\s*"
    r"(?:[HL*]\b\s*)?"
    r"(?:\(?\s*(?:ref(?:erence)?(?:\s*range)?\s*[:\-]?\s*)?(?P<range>\d+(?:\.\d+)?\s*[-–]\s*\d+(?:\.\d+)?|[<>]\s*\d+(?:\.\d+)?)\s*\)?)?",
    re.I,
)


def report_type_of(text: str) -> str:
    t = (text or "").lower()
    for rx, name in REPORT_TYPES:
        if re.search(rx, t):
            return name
    return ""


def _lines(text: str) -> list[str]:
    return [l.strip() for l in (text or "").splitlines() if l.strip()]


def _in(part: str, line: str) -> bool:
    return not part or norm(part) in norm(line) or norm(part).replace(" ", "") in norm(line).replace(" ", "")


def _verified(v: dict, lines: list[str]) -> dict | None:
    """Keep a value only if everything in it is printed on its source line."""
    if not isinstance(v, dict):
        return None
    v = {k: str(v.get(k) or "").strip() for k in ALLOWED_KEYS}   # drops flag / interpretation / status keys
    line = next((l for l in lines if norm(v["source_line"]) and norm(v["source_line"]) in norm(l)), None)
    if line is None or not v["value"] or not _in(v["value"], line):
        return None
    name_first = re.findall(r"[a-z0-9]+", v["name"].lower())
    display_ok = v["name"] in SHORT_NAMES.values() and any(k in line.lower() for k, s in SHORT_NAMES.items()
                                                            if s == v["name"])
    if not name_first or not (name_first[0] in line.lower() or display_ok):
        return None
    if not _in(v["unit"], line):
        v["unit"] = ""
    if not _in(v["reference_range_as_printed"], line):
        v["reference_range_as_printed"] = ""
    v["source_line"] = line
    return v


def rule_based_extract(report_text: str) -> dict:
    values = []
    for line in _lines(report_text):
        m = LINE_RE.match(line)
        if not m or find_date(line, prefer="past")[0]:   # date / header lines are not values
            continue
        name = m.group("name").strip()
        # skip header-ish lines like "Date 20" or "Page 1"
        if name.lower() in {"date", "page", "age", "sample", "sample no", "id", "patient id", "uhid"}:
            continue
        values.append({
            "name": SHORT_NAMES.get(name.lower(), name),
            "value": m.group("value"),
            "unit": (m.group("unit") or "").strip(),
            "reference_range_as_printed": (m.group("range") or "").strip(),
            "source_line": line,
        })
    return {"values": values}


def extract_report_values(report_text: str) -> dict:
    """(report_text) -> ReportExtraction. Never raises."""
    try:
        lines = _lines(report_text)
        out = call_json(load_prompt("extract"), report_text)
        ai_ok = bool(out and isinstance(out.get("values"), list))
        if not ai_ok:
            out = rule_based_extract(report_text)
        values = [v for v in (_verified(x, lines) for x in out.get("values", [])) if v]
        rdate = str(out.get("report_date") or "") if ai_ok else ""
        if not valid_iso(rdate):
            rdate = find_date(report_text, prefer="past")[0] or ""
        return {
            "ok": ai_ok,
            "report_type": (out.get("report_type") if ai_ok else "") or report_type_of(report_text),
            "report_date": rdate,
            "values": values,
        }
    except Exception as e:  # noqa: BLE001
        print(f"[ai.extract] error: {e}")
        return dict(FALLBACK)
