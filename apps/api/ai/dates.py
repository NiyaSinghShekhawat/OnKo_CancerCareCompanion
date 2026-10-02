"""Date helpers shared by the AI modules. Pure text -> ISO date. No clinical logic."""
import re
from datetime import date, timedelta
from ai.client import today_ist

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
_MON = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"

# Order matters: most specific first. Each pattern's match is also used to strip the date from titles.
DATE_PATTERNS = [
    ("iso", re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")),
    ("dmy_text", re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?" + _MON + r"(?:,?\s+(\d{4}))?", re.I)),
    ("mdy_text", re.compile(r"\b" + _MON + r"\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(\d{4}))?\b", re.I)),
    # 15/10, 15/10/26, 15-10-2026. Not "4-11" or "4.1" (those are lab ranges / values).
    ("dmy_num", re.compile(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b")),
    ("dmy_num", re.compile(r"\b(\d{1,2})-(\d{1,2})-(\d{2,4})\b")),
    ("rel", re.compile(r"\b(today|tomorrow|day after tomorrow)\b", re.I)),
]


def _mon(s: str) -> int:
    return MONTHS[s.lower()[:3]]


def _build(y: int | None, m: int, d: int, today: date, prefer: str) -> date | None:
    try:
        if y is not None:
            if y < 100:
                y += 2000
            return date(y, m, d)
        guess = date(today.year, m, d)
    except ValueError:
        return None
    # No year written: pick the closest sensible year.
    if prefer == "future" and guess < today - timedelta(days=14):
        guess = guess.replace(year=today.year + 1)
    elif prefer == "past" and guess > today + timedelta(days=1):
        guess = guess.replace(year=today.year - 1)
    return guess


def find_date(text: str, prefer: str = "future", today: date | None = None) -> tuple[str | None, str | None]:
    """Return (iso_date, matched_text) for the first date found in `text`, else (None, None).

    prefer='future' for plans ("chemo on 15 Oct"), 'past' for reports ("CBC, 20 Sep").
    """
    today = today or today_ist().date()
    best = None
    for kind, rx in DATE_PATTERNS:
        for m in rx.finditer(text or ""):
            g = m.groups()
            if kind == "iso":
                dt = _build(int(g[0]), int(g[1]), int(g[2]), today, prefer)
            elif kind == "dmy_text":
                dt = _build(int(g[2]) if g[2] else None, _mon(g[1]), int(g[0]), today, prefer)
            elif kind == "mdy_text":
                dt = _build(int(g[2]) if g[2] else None, _mon(g[0]), int(g[1]), today, prefer)
            elif kind == "dmy_num":
                dt = _build(int(g[2]) if g[2] else None, int(g[1]), int(g[0]), today, prefer)
            else:
                word = g[0].lower()
                dt = today + timedelta(days={"today": 0, "tomorrow": 1}.get(word, 2))
            if dt and (best is None or m.start() < best[1].start()):
                best = (dt, m)
            if dt:
                break  # first valid match of this kind is enough
    if not best:
        return None, None
    return best[0].isoformat(), best[1].group(0)


def valid_iso(s) -> bool:
    try:
        date.fromisoformat(str(s))
        return True
    except ValueError:
        return False


def fmt_short(iso: str | None) -> str:
    """'2026-09-20T09:00:00' -> '20 Sep'. Returns '' if unparseable."""
    if not iso:
        return ""
    try:
        d = date.fromisoformat(str(iso)[:10])
        return f"{d.day:02d} {d.strftime('%b')}"
    except ValueError:
        return ""
