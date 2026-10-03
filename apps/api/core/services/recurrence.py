"""
Expand a CarePlanItem recurrence string into scheduled datetimes. Pure parsing, NO AI.
Supported: "daily HH:MM[, HH:MM ...]" and "every N days". Anything else → one event at start_date 09:00.
"""
import re
from datetime import date, datetime, time, timedelta

DEFAULT_TIME = time(9, 0)
_DAILY = re.compile(r"daily\s+(.+)", re.IGNORECASE)
_EVERY = re.compile(r"every\s+(\d+)\s+days?", re.IGNORECASE)
_HHMM = re.compile(r"(\d{1,2}):(\d{2})")


def parse(recurrence: str | None) -> tuple[int, list[time]] | None:
    """Return (step_days, times) or None if recurrence is null/unparseable."""
    text = (recurrence or "").strip()
    if m := _DAILY.fullmatch(text):
        times = []
        for part in m.group(1).split(","):
            hm = _HHMM.fullmatch(part.strip())
            if not hm or int(hm.group(1)) > 23 or int(hm.group(2)) > 59:
                return None
            times.append(time(int(hm.group(1)), int(hm.group(2))))
        return 1, sorted(set(times))
    if m := _EVERY.fullmatch(text):
        step = int(m.group(1))
        return (step, [DEFAULT_TIME]) if step > 0 else None
    return None


def expand(start_date: str, end_date: str | None, recurrence: str | None) -> list[datetime]:
    """Datetimes from start_date to end_date (inclusive). No end_date → start_date only."""
    start = _to_date(start_date)
    rule = parse(recurrence)
    if rule is None:
        return [datetime.combine(start, DEFAULT_TIME)]
    step, times = rule
    end = max(_to_date(end_date), start) if end_date else start
    out, day = [], start
    while day <= end:
        out.extend(datetime.combine(day, t) for t in times)
        day += timedelta(days=step)
    return out


def _to_date(value: str) -> date:
    return datetime.fromisoformat(value).date()
