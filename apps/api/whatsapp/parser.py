"""Parse patient replies. TODO(Shreyan): handle 'all done', Hindi/Telugu replies, conflicting answers."""
import re


def parse_checklist_reply(text: str) -> list[tuple[int, str]]:
    """'1 done, 2 missed' -> [(1,'COMPLETED'), (2,'REPORTED_MISSED')]"""
    out = []
    for num, word in re.findall(r"(\d+)\s*(done|ok|yes|missed|no|skip)", text.lower()):
        out.append((int(num), "COMPLETED" if word in {"done", "ok", "yes"} else "REPORTED_MISSED"))
    return out


def intent(text: str) -> str:
    t = text.strip().lower()
    if t in {"hi", "hello", "menu", "namaste"}:
        return "MENU"
    if t == "sos" or "🆘" in t:
        return "SOS"
    if re.search(r"\d+\s*(done|ok|yes|missed|no|skip)", t):
        return "CHECKLIST"
    return "QUERY"
