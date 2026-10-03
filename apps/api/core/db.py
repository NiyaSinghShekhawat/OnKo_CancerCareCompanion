"""Database engine for SQLite (local dev, tests) and Postgres (Supabase, deployment).
DATABASE_URL examples:
  sqlite:///./onko.db                                                   (default)
  postgresql+psycopg://postgres.<ref>:<password>@<pooler host>:5432/postgres   (see docs/core.md, Supabase)"""
import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase


def normalize_url(url: str) -> str:
    """Supabase shows postgresql://… (and some tools postgres://…). Use the installed psycopg 3 driver for both;
    without a driver name SQLAlchemy would look for psycopg2, which isn't installed."""
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


def engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}   # FastAPI uses the session from worker threads
    if url.startswith("postgresql"):
        return {"pool_pre_ping": True}   # poolers drop idle connections; test each one before use
    return {}


DATABASE_URL = normalize_url(os.getenv("DATABASE_URL", "sqlite:///./onko.db"))
engine = create_engine(DATABASE_URL, **engine_kwargs(DATABASE_URL))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def init_db():
    from core import models  # noqa: F401  (register tables)
    Base.metadata.create_all(bind=engine)
    _add_missing_columns()


def add_column_ddl(table, col, dialect) -> str | None:
    """Standard ALTER TABLE … ADD COLUMN for any dialect, or None if the column can't be added in place.
    Nullable → existing rows get NULL. server_default → existing rows get that value (NOT NULL DEFAULT …).
    NOT NULL without a server default → None (needs a reseed)."""
    quote = dialect.identifier_preparer.quote
    ddl = f"ALTER TABLE {quote(table.name)} ADD COLUMN {quote(col.name)} {col.type.compile(dialect=dialect)}"
    if col.server_default is not None:
        default = col.server_default.arg
        return f"{ddl} NOT NULL DEFAULT {getattr(default, 'text', default)}"
    return ddl if col.nullable else None


def _add_missing_columns():
    """create_all never alters existing tables. Add columns that a model change introduced, in place, using
    SQLAlchemy's inspector (no SQLite PRAGMAs), so an existing onko.db or Supabase database keeps working."""
    existing = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            have = {c["name"] for c in existing.get_columns(table.name)}
            for col in table.columns:
                if col.name not in have and (ddl := add_column_ddl(table, col, engine.dialect)):
                    conn.execute(text(ddl))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
