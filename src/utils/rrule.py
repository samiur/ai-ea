# ABOUTME: RRULE (iCal recurrence) parsing, validation, and expansion
# ABOUTME: Thin typed wrapper over dateutil.rrule for series cadence math

from datetime import UTC, datetime

from dateutil.rrule import rrule, rrulestr


def _parse(rule: str, dtstart: datetime | None = None) -> rrule:
    parsed = rrulestr(rule, dtstart=dtstart)
    if not isinstance(parsed, rrule):
        raise ValueError(f"Invalid RRULE (rule sets unsupported): {rule!r}")
    return parsed


def validate_rrule(rule: str) -> str:
    """Validate an RRULE string, returning it unchanged.

    Raises ValueError with an 'RRULE' message for invalid rules.
    """
    try:
        _parse(rule)
    except (ValueError, TypeError, KeyError) as exc:
        raise ValueError(f"Invalid RRULE {rule!r}: {exc}") from exc
    return rule


def next_occurrence(rule: str, after: datetime) -> datetime | None:
    """Get the first occurrence strictly after the given moment."""
    parsed = _parse(rule, dtstart=after.replace(tzinfo=None))
    nxt = parsed.after(after.replace(tzinfo=None), inc=False)
    if nxt is None:
        return None
    return nxt.replace(tzinfo=after.tzinfo or UTC)


def expand_series(rule: str, start: datetime, end: datetime) -> list[datetime]:
    """List all occurrences within [start, end], inclusive."""
    parsed = _parse(rule, dtstart=start.replace(tzinfo=None))
    naive = parsed.between(start.replace(tzinfo=None), end.replace(tzinfo=None), inc=True)
    tz = start.tzinfo or UTC
    return [d.replace(tzinfo=tz) for d in naive]
