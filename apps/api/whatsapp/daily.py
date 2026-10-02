"""Send today's ONE WhatsApp checklist to every patient whose journey state allows messaging.

Run it once each morning from a scheduler (Render Cron Job, Railway cron, GitHub Actions…):

    cd apps/api && python -m whatsapp.daily            # send for real (dry-run without Twilio keys)
    cd apps/api && python -m whatsapp.daily --preview  # print who would get what, send nothing

It talks to the database directly, so it needs the same DATABASE_URL as the API (Supabase/Postgres when deployed).
"""
import argparse
import os
import sys

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))

from core.db import SessionLocal, init_db  # noqa: E402
from core.models import Patient  # noqa: E402
from core.services import checklist  # noqa: E402
from core.services.journey_state import can_message  # noqa: E402
from whatsapp.messages import mask_phone  # noqa: E402
from whatsapp.webhook import deliver_checklist  # noqa: E402


def run(preview: bool = False) -> dict:
    init_db()
    db = SessionLocal()
    summary = {"sent": 0, "not_sent": 0, "skipped_journey_state": 0, "no_items_today": 0}
    try:
        for p in db.query(Patient).order_by(Patient.id).all():
            if not can_message(p.journey_state):
                summary["skipped_journey_state"] += 1
                continue
            items, _ = checklist.todays_items(db, p.id)
            if not items:
                summary["no_items_today"] += 1      # one daily message, and none at all on empty days
                continue
            if preview:
                print(f"would send {len(items)} item(s) to {p.id} ({mask_phone(p.phone_whatsapp)})")
                continue
            out = deliver_checklist(db, p)
            summary["sent" if out.get("sent") else "not_sent"] += 1
            if not out.get("sent"):
                print(f"{p.id}: not sent — {out.get('error') or out.get('reason')}")
    finally:
        db.close()
    print(f"[whatsapp.daily] {summary}")
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--preview", action="store_true", help="list recipients without sending")
    run(ap.parse_args().preview)
    sys.exit(0)
