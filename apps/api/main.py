"""
OnKo API entrypoint.
SHARED FILE — written in Phase 0. All routers are already registered.
Do not edit without telling the whole team.
"""
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from core.db import init_db
from core.routers import (
    patients, careplan, events, attention, queries, reports, sos, caregivers, audit,
)
from whatsapp import webhook as whatsapp_webhook

app = FastAPI(title="OnKo API", version="0.1.0",
              description="The doctor decides the care. OnKo keeps the journey connected.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

@app.on_event("startup")
def _startup():
    init_db()

@app.get("/health")
def health():
    return {"ok": True}

# --- core (Samprada) ---
app.include_router(patients.router)
app.include_router(careplan.router)
app.include_router(events.router)
app.include_router(attention.router)
app.include_router(queries.router)
app.include_router(reports.router)
app.include_router(sos.router)
app.include_router(caregivers.router)
app.include_router(audit.router)

# --- whatsapp (Shreyan) ---
app.include_router(whatsapp_webhook.router)
