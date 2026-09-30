"""Outgoing WhatsApp text. Owner: Shreyan.

- One consolidated checklist per day, never one message per activity.
- Every send goes through can_message(journey_state) first (the webhook / send routes check it).
- Tone changes with journey state: PALLIATIVE gets no adherence-style pressure.
- Templates exist in English, Hindi, Telugu, Tamil; item titles stay exactly as the doctor approved them.
"""
import os
import time

from ai.client import today_ist
from core.models import Caregiver, Patient
from core.services.journey_state import can_message

T = {
    "English": {
        "header": "Namaste {name}, here is today's care checklist from your care team:",
        "footer": "Reply with the number and done / missed, e.g. *1 done, 2 missed* (or *all done*).\n"
                  "You can update this for 24 hours. Reply HI for menu, SOS for urgent help.",
        "header_gentle": "Namaste {name}, here is today's plan from your care team:",
        "footer_gentle": "Reply any time if you'd like to update it. Reply HI for menu, SOS for help.",
        "menu": "OnKo menu:\n1️⃣ Today's medicines\n2️⃣ Ask a question / need help\n"
                "🆘 Reply SOS for urgent help — your caregiver and care team will be alerted.",
        "sos_ack": "Your SOS has been sent to your care team. If you need immediate medical help, call 108.",
        "sos_ack_cg": "Your SOS has been sent to your care team and your caregiver. "
                      "If you need immediate medical help, call 108.",
        "query_prompt": "Please type your question or what you need. It will be shared with your care team.",
        "query_ack": "Thanks, your message has been shared with your care team. They will get back to you.",
        "recorded": "Recorded:", "thanks": "Thank you.",
        "done": "done ✅", "missed": "missed ❌", "conflicting": "both answers received — your care team will check",
        "delayed": "(late reply)",
        "unknown": "Item {nums} isn't on today's checklist.",
        "no_items": "You have no care activities scheduled for today.",
        "meds": "Today's medicines:", "no_meds": "No medicines scheduled for today.",
        "paused": "Your message has been passed to your care team.",
        "optout": "Your request to stop WhatsApp messages has been passed to your care team.",
    },
    "Hindi": {
        "header": "नमस्ते {name}, आपकी केयर टीम की ओर से आज की चेकलिस्ट:",
        "footer": "नंबर के साथ जवाब दें, जैसे: *1 done, 2 missed* (या *all done* / *sab ho gaya*)।\n"
                  "आप 24 घंटे तक अपडेट कर सकते हैं। मेन्यू के लिए HI, तुरंत मदद के लिए SOS भेजें।",
        "header_gentle": "नमस्ते {name}, आपकी केयर टीम की ओर से आज की योजना:",
        "footer_gentle": "जब चाहें अपडेट भेज सकते हैं। मेन्यू के लिए HI, मदद के लिए SOS भेजें।",
        "menu": "OnKo मेन्यू:\n1️⃣ आज की दवाइयाँ\n2️⃣ सवाल पूछें / मदद चाहिए\n"
                "🆘 तुरंत मदद के लिए SOS भेजें — आपके केयरगिवर और केयर टीम को सूचना दी जाएगी।",
        "sos_ack": "आपका SOS आपकी केयर टीम को भेज दिया गया है। तुरंत चिकित्सा सहायता के लिए 108 पर कॉल करें।",
        "sos_ack_cg": "आपका SOS आपकी केयर टीम और केयरगिवर को भेज दिया गया है। "
                      "तुरंत चिकित्सा सहायता के लिए 108 पर कॉल करें।",
        "query_prompt": "कृपया अपना सवाल या ज़रूरत लिखें। इसे आपकी केयर टीम तक पहुँचाया जाएगा।",
        "query_ack": "धन्यवाद, आपका संदेश आपकी केयर टीम तक पहुँचा दिया गया है। वे आपसे संपर्क करेंगे।",
        "recorded": "दर्ज किया गया:", "thanks": "धन्यवाद।",
        "done": "हो गया ✅", "missed": "छूट गया ❌", "conflicting": "दोनों जवाब मिले — केयर टीम देखेगी",
        "delayed": "(देर से जवाब)",
        "unknown": "आइटम {nums} आज की चेकलिस्ट में नहीं है।",
        "no_items": "आज आपकी कोई केयर गतिविधि निर्धारित नहीं है।",
        "meds": "आज की दवाइयाँ:", "no_meds": "आज कोई दवा निर्धारित नहीं है।",
        "paused": "आपका संदेश आपकी केयर टीम तक पहुँचा दिया गया है।",
        "optout": "WhatsApp संदेश बंद करने का आपका अनुरोध केयर टीम तक पहुँचा दिया गया है।",
    },
    "Telugu": {
        "header": "నమస్కారం {name}, మీ కేర్ టీమ్ నుండి ఈరోజు చెక్‌లిస్ట్:",
        "footer": "నంబర్‌తో జవాబు ఇవ్వండి, ఉదా: *1 done, 2 missed* (లేదా *all done*).\n"
                  "24 గంటల వరకు అప్‌డేట్ చేయవచ్చు. మెనూ కోసం HI, వెంటనే సహాయం కోసం SOS పంపండి.",
        "header_gentle": "నమస్కారం {name}, మీ కేర్ టీమ్ నుండి ఈరోజు ప్రణాళిక:",
        "footer_gentle": "ఎప్పుడైనా అప్‌డేట్ పంపవచ్చు. మెనూ కోసం HI, సహాయం కోసం SOS పంపండి.",
        "menu": "OnKo మెనూ:\n1️⃣ ఈరోజు మందులు\n2️⃣ ప్రశ్న అడగండి / సహాయం కావాలి\n"
                "🆘 వెంటనే సహాయం కోసం SOS పంపండి — మీ కేర్‌గివర్ మరియు కేర్ టీమ్‌కు తెలియజేయబడుతుంది.",
        "sos_ack": "మీ SOS మీ కేర్ టీమ్‌కు పంపబడింది. తక్షణ వైద్య సహాయం కోసం 108కు కాల్ చేయండి.",
        "sos_ack_cg": "మీ SOS మీ కేర్ టీమ్‌కు మరియు కేర్‌గివర్‌కు పంపబడింది. "
                      "తక్షణ వైద్య సహాయం కోసం 108కు కాల్ చేయండి.",
        "query_prompt": "దయచేసి మీ ప్రశ్న లేదా అవసరాన్ని టైప్ చేయండి. ఇది మీ కేర్ టీమ్‌కు పంపబడుతుంది.",
        "query_ack": "ధన్యవాదాలు, మీ సందేశం మీ కేర్ టీమ్‌కు పంపబడింది. వారు మిమ్మల్ని సంప్రదిస్తారు.",
        "recorded": "నమోదు చేయబడింది:", "thanks": "ధన్యవాదాలు.",
        "done": "పూర్తయింది ✅", "missed": "మిస్ అయింది ❌",
        "conflicting": "రెండు జవాబులు వచ్చాయి — కేర్ టీమ్ చూస్తుంది", "delayed": "(ఆలస్యంగా జవాబు)",
        "unknown": "అంశం {nums} ఈరోజు చెక్‌లిస్ట్‌లో లేదు.",
        "no_items": "ఈరోజు మీకు ఎలాంటి కేర్ కార్యకలాపాలు లేవు.",
        "meds": "ఈరోజు మందులు:", "no_meds": "ఈరోజు మందులు ఏవీ లేవు.",
        "paused": "మీ సందేశం మీ కేర్ టీమ్‌కు పంపబడింది.",
        "optout": "WhatsApp సందేశాలు ఆపమని మీ అభ్యర్థన కేర్ టీమ్‌కు పంపబడింది.",
    },
    "Tamil": {
        "header": "வணக்கம் {name}, உங்கள் பராமரிப்புக் குழுவிடமிருந்து இன்றைய சரிபார்ப்புப் பட்டியல்:",
        "footer": "எண்ணுடன் பதில் அனுப்பவும், எ.கா: *1 done, 2 missed* (அல்லது *all done*).\n"
                  "24 மணி நேரம் வரை புதுப்பிக்கலாம். மெனுவுக்கு HI, உடனடி உதவிக்கு SOS அனுப்பவும்.",
        "header_gentle": "வணக்கம் {name}, உங்கள் பராமரிப்புக் குழுவிடமிருந்து இன்றைய திட்டம்:",
        "footer_gentle": "எப்போது வேண்டுமானாலும் புதுப்பிக்கலாம். மெனுவுக்கு HI, உதவிக்கு SOS அனுப்பவும்.",
        "menu": "OnKo மெனு:\n1️⃣ இன்றைய மருந்துகள்\n2️⃣ கேள்வி கேட்க / உதவி தேவை\n"
                "🆘 உடனடி உதவிக்கு SOS அனுப்பவும் — உங்கள் பராமரிப்பாளருக்கும் பராமரிப்புக் குழுவுக்கும் தெரிவிக்கப்படும்.",
        "sos_ack": "உங்கள் SOS உங்கள் பராமரிப்புக் குழுவுக்கு அனுப்பப்பட்டது. உடனடி மருத்துவ உதவிக்கு 108-ஐ அழைக்கவும்.",
        "sos_ack_cg": "உங்கள் SOS உங்கள் பராமரிப்புக் குழுவுக்கும் பராமரிப்பாளருக்கும் அனுப்பப்பட்டது. "
                      "உடனடி மருத்துவ உதவிக்கு 108-ஐ அழைக்கவும்.",
        "query_prompt": "உங்கள் கேள்வி அல்லது தேவையைத் தட்டச்சு செய்யவும். இது உங்கள் பராமரிப்புக் குழுவுக்கு அனுப்பப்படும்.",
        "query_ack": "நன்றி, உங்கள் செய்தி உங்கள் பராமரிப்புக் குழுவுக்கு அனுப்பப்பட்டது. அவர்கள் உங்களைத் தொடர்புகொள்வார்கள்.",
        "recorded": "பதிவு செய்யப்பட்டது:", "thanks": "நன்றி.",
        "done": "முடிந்தது ✅", "missed": "தவறியது ❌",
        "conflicting": "இரண்டு பதில்கள் வந்தன — பராமரிப்புக் குழு பார்க்கும்", "delayed": "(தாமதமான பதில்)",
        "unknown": "உருப்படி {nums} இன்றைய பட்டியலில் இல்லை.",
        "no_items": "இன்று உங்களுக்கு எந்தப் பராமரிப்புச் செயல்பாடும் திட்டமிடப்படவில்லை.",
        "meds": "இன்றைய மருந்துகள்:", "no_meds": "இன்று மருந்துகள் எதுவும் திட்டமிடப்படவில்லை.",
        "paused": "உங்கள் செய்தி உங்கள் பராமரிப்புக் குழுவுக்கு அனுப்பப்பட்டது.",
        "optout": "WhatsApp செய்திகளை நிறுத்தும் உங்கள் கோரிக்கை பராமரிப்புக் குழுவுக்கு அனுப்பப்பட்டது.",
    },
}

STATE_KEY = {"COMPLETED": "done", "REPORTED_MISSED": "missed", "CONFLICTING": "conflicting"}
ICON = {"COMPLETED": "✅", "REPORTED_MISSED": "❌", "NO_RESPONSE": "⏳", "CONFLICTING": "⚠️"}


def lang(patient) -> str:
    if os.getenv("WHATSAPP_FORCE_ENGLISH", "").lower() in {"1", "true", "yes"}:
        return "English"
    l = (getattr(patient, "preferred_language", None) or "English").strip().title()
    return l if l in T else "English"


def t(patient, key: str, **kw) -> str:
    return T[lang(patient)][key].format(**kw)


def first_name(patient) -> str:
    return (patient.name or "").split()[0] if patient.name else ""


def _time(it: dict) -> str:
    at = str(it.get("scheduled_at") or "")
    return at[11:16] if len(at) >= 16 else ""


def render_checklist(patient, items: list[dict]) -> str:
    """ONE consolidated message. `patient` is a Patient row (old signature took a name string — still accepted)."""
    if isinstance(patient, str):   # backwards compatible with the Phase 0 stub
        patient = Patient(name=patient, preferred_language="English", journey_state="ACTIVE_TREATMENT")
    gentle = patient.journey_state == "PALLIATIVE"   # comfort-care tone: no adherence-style pressure
    name = first_name(patient)
    if not items:
        return f"{t(patient, 'header_gentle' if gentle else 'header', name=name)}\n\n{t(patient, 'no_items')}"
    lines = [t(patient, "header_gentle" if gentle else "header", name=name), ""]
    for i, it in enumerate(items, 1):
        tm = _time(it)
        lines.append(f"{i}. {it['title']}" + (f" — {tm}" if tm else ""))
    lines += ["", t(patient, "footer_gentle" if gentle else "footer")]
    return "\n".join(lines)


def render_menu(patient) -> str:
    return t(patient, "menu")


def render_meds(patient, items: list[dict]) -> str:
    meds = [(i, it) for i, it in enumerate(items, 1) if it.get("type") == "MEDICATION"]
    if not meds:
        return t(patient, "no_meds")
    lines = [t(patient, "meds")]
    for i, it in meds:
        icon = ICON.get(it.get("status"), "")
        tm = _time(it)
        lines.append(f"{i}. {it['title']}" + (f" — {tm}" if tm else "") + (f" {icon}" if icon else ""))
    return "\n".join(lines)


def render_recorded(patient, recorded: list[tuple[int, str, str, bool]], unknown: list[int]) -> str:
    """recorded = [(number, title, state, was_late)]"""
    lines = []
    if recorded:
        lines.append(t(patient, "recorded"))
        for n, title, state, late in recorded:
            lines.append(f"{n}. {title} — {t(patient, STATE_KEY[state])}" + (f" {t(patient, 'delayed')}" if late else ""))
    if unknown:
        lines.append(t(patient, "unknown", nums=", ".join(str(n) for n in unknown)))
    if recorded:
        lines.append(t(patient, "thanks"))
    return "\n".join(lines)


# ---------------- sending ----------------

def send(to: str, body: str) -> bool:
    """Send one WhatsApp message via Twilio. Without Twilio keys it prints instead (dry run). Never raises."""
    sid, token = os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN")
    if not sid or not token:
        print(f"[whatsapp:dry-run] -> {to}\n{body}\n")
        return False
    try:
        from twilio.rest import Client
        Client(sid, token).messages.create(from_=os.getenv("TWILIO_WHATSAPP_FROM"), to=to, body=body)
        return True
    except Exception as e:  # noqa: BLE001
        print(f"[whatsapp] send to {to} failed: {e}")
        return False


_recent_sos: dict[str, float] = {}
SOS_DEDUPE_SECONDS = 60


def notify_caregivers(db, patient: Patient, channel: str = "whatsapp") -> list[str]:
    """Alert caregivers who GRANTED consent and have receive_escalations on. Returns names notified.

    Safe to call twice for the same SOS (e.g. from the webhook and from core's sos.py): a second call within
    60 s for the same patient is ignored.
    """
    if not can_message(patient.journey_state):
        return []
    now = time.time()
    if now - _recent_sos.get(patient.id, 0) < SOS_DEDUPE_SECONDS:
        return []
    _recent_sos[patient.id] = now
    notified = []
    cgs = db.query(Caregiver).filter_by(patient_id=patient.id, consent_status="GRANTED").all()
    for cg in cgs:
        if not (cg.permissions or {}).get("receive_escalations"):
            continue
        body = (f"OnKo alert: {patient.name} pressed SOS via {channel} at {today_ist():%H:%M, %d %b}. "
                f"Their care team has been notified. Please check on them. "
                f"If immediate medical help is needed, call 108.")
        send(cg.phone_whatsapp, body)
        notified.append(cg.name)
    return notified


MENU = T["English"]["menu"]   # kept for anything importing the Phase 0 constant
