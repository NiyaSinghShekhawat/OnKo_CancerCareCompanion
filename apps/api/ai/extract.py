"""Report extraction — values exactly as printed. No interpretation."""
import re
from ai.client import call_json, load_prompt

FALLBACK = {"ok": False, "report_type": "", "report_date": "", "values": []}


def extract_report_values(report_text: str) -> dict:
    out = call_json(load_prompt("extract"), report_text)
    if not out or "values" not in out:
        return FALLBACK
    # keep only values that literally appear in the source text
    out["values"] = [v for v in out["values"] if str(v.get("value", "")) and str(v["value"]) in report_text]
    for v in out["values"]:
        v.pop("flag", None); v.pop("interpretation", None); v.pop("status", None)
    out["ok"] = True
    return out
