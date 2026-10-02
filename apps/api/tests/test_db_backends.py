"""Postgres (Supabase) support in core/db.py, checked against SQLAlchemy's Postgres dialect without a server.
The test suite itself always runs on SQLite (test_onko.db, set in conftest.py)."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.schema import CreateTable

from core import models  # noqa: F401  (register tables)
from core.db import Base, add_column_ddl, engine, engine_kwargs, normalize_url

PG = "postgresql+psycopg://postgres.abcdefgh:p%40ss@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"


def test_tests_run_on_sqlite():
    assert engine.dialect.name == "sqlite" and "test_onko.db" in str(engine.url)


@pytest.mark.parametrize("url, expected", [
    ("postgresql://u:p@h:5432/postgres", "postgresql+psycopg://u:p@h:5432/postgres"),
    ("postgres://u:p@h:5432/postgres", "postgresql+psycopg://u:p@h:5432/postgres"),
    (PG, PG),
    ("sqlite:///./onko.db", "sqlite:///./onko.db"),
])
def test_normalize_url(url, expected):
    assert normalize_url(url) == expected


def test_engine_kwargs_per_backend():
    assert engine_kwargs("sqlite:///./onko.db") == {"connect_args": {"check_same_thread": False}}
    assert engine_kwargs(PG) == {"pool_pre_ping": True}          # no check_same_thread for Postgres


def test_postgres_engine_uses_psycopg_and_pre_ping():
    pg = create_engine(PG, **engine_kwargs(PG))                  # no connection is made here
    assert (pg.dialect.name, pg.dialect.driver) == ("postgresql", "psycopg")
    assert pg.pool._pre_ping is True
    pg.dispose()


@pytest.mark.parametrize("dialect", [postgresql.dialect(), sqlite.dialect()], ids=["postgresql", "sqlite"])
def test_every_table_compiles(dialect):
    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=dialect))
        assert ddl.startswith("\nCREATE TABLE") and "PRAGMA" not in ddl


@pytest.mark.parametrize("table, col, pg_ddl", [
    ("patients", "journey_chapter", "ALTER TABLE patients ADD COLUMN journey_chapter INTEGER NOT NULL DEFAULT 1"),
    ("care_events", "journey_chapter", "ALTER TABLE care_events ADD COLUMN journey_chapter INTEGER NOT NULL DEFAULT 1"),
    ("patients", "journey_state_changed_at",
     "ALTER TABLE patients ADD COLUMN journey_state_changed_at TIMESTAMP WITHOUT TIME ZONE"),
    ("patients", "previous_journey_state", "ALTER TABLE patients ADD COLUMN previous_journey_state VARCHAR"),
])
def test_add_column_ddl_is_standard_sql(table, col, pg_ddl):
    t = Base.metadata.tables[table]
    assert add_column_ddl(t, t.c[col], postgresql.dialect()) == pg_ddl
    lite = add_column_ddl(t, t.c[col], sqlite.dialect())
    assert lite.startswith(f"ALTER TABLE {table} ADD COLUMN {col} ") and "PRAGMA" not in lite


def test_inviting_for_unknown_patient_is_404_not_an_orphan_row():
    """Postgres enforces caregivers.patient_id → patients.id; SQLite would silently store an orphan."""
    from fastapi.testclient import TestClient
    from core import seed
    from core.db import SessionLocal
    from core.models import Caregiver
    from main import app
    seed.run()
    r = TestClient(app).post("/patients/p_nobody/caregivers", headers={"X-Role": "doctor", "X-User-Id": "doc_mehta"},
                             json={"name": "X", "relation": "Son", "phone_whatsapp": "whatsapp:+910000000098"})
    assert r.status_code == 404
    s = SessionLocal()
    assert s.query(Caregiver).filter_by(patient_id="p_nobody").count() == 0
    s.close()


def test_not_null_column_without_default_is_skipped():
    t = Base.metadata.tables["patients"]
    assert add_column_ddl(t, t.c["name"], postgresql.dialect()) is None
