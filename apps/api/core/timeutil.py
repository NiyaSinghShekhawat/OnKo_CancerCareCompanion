"""One clock for core. Stored datetimes are naive UTC (no tzinfo), exactly what datetime.utcnow() used to give,
without its deprecation warning."""
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
