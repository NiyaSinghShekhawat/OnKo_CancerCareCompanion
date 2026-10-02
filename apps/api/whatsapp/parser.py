"""Parse patient replies. Pure text -> structure. No clinical logic, no severity, no emergency inference.

Understands English, Hinglish / Hindi, and common romanised Telugu / Tamil replies, plus ✅ / ❌ / 👍.
"""
import re

# Longest phrases first so "nahi liya" beats "liya".
DONE_PHRASES = [
    "ho gaya", "ho gayi", "hogaya", "kar liya", "kar li", "le liya", "le li", "kha liya", "kha li", "li hai", "liya hai",
    "vesukunna", "ayyindi", "aipoyindi", "saapten", "mudinjathu", "mudinchu",
    "हो गया", "हो गई", "ले लिया", "ले ली", "कर लिया", "खा ली", "हाँ", "हां",
    "done", "completed", "complete", "taken", "took", "yes", "yep", "yeah", "ok", "okay", "haan", "han", "ha", "liya",
    "✅", "✔️", "✔", "👍", "☑️",
]
MISS_PHRASES = [
    "nahi liya", "nahi li", "nahin liya", "nahi kiya", "nahi hua", "bhool gaya", "bhool gayi", "bhul gaya", "chhoot gaya",
    "chhut gaya", "reh gaya", "marchipoya", "vesukoledu", "saapidala", "marandhuten",
    "नहीं लिया", "नहीं ली", "नहीं किया", "भूल गया", "भूल गई", "छूट गया", "छूट गई", "नहीं",
    "missed", "miss", "not taken", "not done", "skipped", "skip", "no", "nope", "nahi", "nahin", "nai", "ledu", "illa",
    "❌", "✖️", "✖", "👎",
]
ALL_WORDS = r"(all|everything|sab|sabhi|saare|sare|anni|ella|ellam)"
MENU_WORDS = {"hi", "hii", "hello", "hey", "menu", "namaste", "namaskar", "namaskaram", "vanakkam", "start", "helo"}
OPTOUT_WORDS = {"stop", "unsubscribe", "stop messages", "band karo"}
DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

DONE, MISS = "COMPLETED", "REPORTED_MISSED"


def _phrase_rx(phrases: list[str]) -> str:
    parts = []
    for p in phrases:
        e = re.escape(p)
        ascii_word = p[0].isascii() and p[0].isalnum()      # \b is unreliable around Devanagari vowel signs
        parts.append(rf"\b{e}\b" if ascii_word else e)
    return "(" + "|".join(parts) + ")"


_DONE_RX = re.compile(_phrase_rx(DONE_PHRASES), re.I)
_MISS_RX = re.compile(_phrase_rx(MISS_PHRASES), re.I)


def normalise(text: str) -> str:
    t = (text or "").translate(DEVANAGARI_DIGITS).lower().strip()
    return re.sub(r"\s+", " ", t)


def _tokenise(t: str) -> str:
    """Replace done / missed phrases with the tokens ⟨D⟩ / ⟨M⟩ (missed first: 'nahi liya' contains 'liya')."""
    t = _MISS_RX.sub(" ⟨M⟩ ", t)
    t = _DONE_RX.sub(" ⟨D⟩ ", t)
    return re.sub(r"\s+", " ", t).strip()


_NUMS = r"\d{1,2}(?:\s*(?:,|&|and|aur|\+|/)?\s*\d{1,2})*"
_AFTER = re.compile(rf"(?P<nums>{_NUMS})\s*[:\-=.)]?\s*(?P<st>⟨[DM]⟩)")       # "1 done", "1,2 done", "1- ✅"
# "done: 1, 2" — but not "took 2 tablets" (number followed by a word is not a checklist answer)
_BEFORE = re.compile(rf"(?P<st>⟨[DM]⟩)\s*[:\-=]?\s*(?P<nums>{_NUMS})\b(?!\s*[^\W\d_])")


def parse_checklist_reply(text: str) -> list[tuple[int, str]]:
    """'1 done, 2 missed' -> [(1,'COMPLETED'), (2,'REPORTED_MISSED')]

    The same number given both answers -> (n, 'CONFLICTING'). 'all done' is handled by parse_all().
    """
    t = _tokenise(normalise(text))
    answers: dict[int, set[str]] = {}
    matches = list(_AFTER.finditer(t)) or list(_BEFORE.finditer(t))
    for m in matches:
        state = DONE if m.group("st") == "⟨D⟩" else MISS
        for n in re.findall(r"\d{1,2}", m.group("nums")):
            answers.setdefault(int(n), set()).add(state)
    return [(n, "CONFLICTING" if len(s) > 1 else s.pop()) for n, s in sorted(answers.items())]


def parse_all(text: str) -> str | None:
    """'all done' / 'sab ho gaya' / '✅ all' -> 'COMPLETED'; 'all missed' -> 'REPORTED_MISSED'; else None."""
    t = _tokenise(normalise(text))
    if re.search(r"\d", t) or not re.search(rf"\b{ALL_WORDS}\b", t):
        return None
    has_d, has_m = "⟨D⟩" in t, "⟨M⟩" in t
    if has_d and not has_m:
        return DONE
    if has_m and not has_d:
        return MISS
    return None


def intent(text: str) -> str:
    """MENU | SOS | MENU_MEDS | MENU_QUERY | CHECKLIST | OPT_OUT | QUERY"""
    t = normalise(text).strip(" .!?")
    if t in MENU_WORDS:
        return "MENU"
    if t == "sos" or "🆘" in t or re.fullmatch(r"sos\W*|\W*sos", t):
        return "SOS"
    if t in OPTOUT_WORDS:
        return "OPT_OUT"
    if t in {"1", "1️⃣", "one", "medication", "medicine", "medicines", "dawai"}:
        return "MENU_MEDS"
    if t in {"2", "2️⃣", "two", "query", "help", "question"}:
        return "MENU_QUERY"
    if parse_checklist_reply(text) or parse_all(text):
        return "CHECKLIST"
    return "QUERY"
