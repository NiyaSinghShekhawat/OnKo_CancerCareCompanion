import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./onko.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def init_db():
    from core import models  # noqa: F401  (register tables)
    Base.metadata.create_all(bind=engine)
    _add_missing_columns()


def _add_missing_columns():
    """create_all never alters existing tables. Add new columns in place so an existing onko.db keeps working
    after a model change: nullable ones stay NULL, ones with a server_default get that value on existing rows."""
    from sqlalchemy import inspect, text
    existing = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            have = {c["name"] for c in existing.get_columns(table.name)}
            for col in table.columns:
                if col.name in have:
                    continue
                ddl = f"ALTER TABLE {table.name} ADD COLUMN {col.name} {col.type.compile(engine.dialect)}"
                if col.server_default is not None:
                    ddl += f" NOT NULL DEFAULT {col.server_default.arg}"
                elif not col.nullable:
                    continue   # can't add a NOT NULL column without a default; needs a reseed
                conn.execute(text(ddl))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
