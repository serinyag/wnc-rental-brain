from __future__ import annotations

"""Deterministic rental-date normalization from timestamped inbound evidence.

No wall-clock lookup, provider call or case mutation. The caller persists the
returned provenance on the observation and uses the normal intake/change path.
"""
from datetime import date, datetime, time, timedelta, timezone
import re
from typing import Any
from zoneinfo import ZoneInfo

VENUE_TIMEZONE = 'Europe/Amsterdam'
MONTHS = {name: n for n, names in enumerate((
    ('january', 'januari', 'jan'), ('february', 'februari', 'feb'), ('march', 'maart', 'mar'),
    ('april', 'apr'), ('may', 'mei'), ('june', 'juni', 'jun'), ('july', 'juli', 'jul'),
    ('august', 'augustus', 'aug'), ('september', 'sep'), ('october', 'oktober', 'oct', 'okt'),
    ('november', 'nov'), ('december', 'dec')), 1) for name in names}
MONTH_PATTERN = '|'.join(sorted(MONTHS, key=len, reverse=True))
DATE_PATTERN = re.compile(
    rf'\b(?:(?P<day>\d{{1,2}})(?:st|nd|rd|th)?\s+(?P<month>{MONTH_PATTERN})(?:\s+(?P<year>\d{{4}}))?'
    rf'|(?P<month_first>{MONTH_PATTERN})\s+(?P<day_last>\d{{1,2}})(?:st|nd|rd|th)?(?:,?\s+(?P<year_last>\d{{4}}))?'
    r'|(?P<iso_year>\d{4})-(?P<iso_month>\d{2})-(?P<iso_day>\d{2}))\b', re.I)


def timing_components(text: str) -> dict[str, Any]:
    """Finite unambiguous calendar/time expressions; no invented missing parts."""
    matches = list(DATE_PATTERN.finditer(text))
    result: dict[str, Any] = {}
    if len(matches) > 1:
        return {'normalization_error': 'multiple_calendar_dates_require_clarification'}
    if matches:
        m = matches[0]
        result = {'day': int(m['day'] or m['day_last'] or m['iso_day']),
                  'month': int(m['iso_month']) if m['iso_month'] else MONTHS[(m['month'] or m['month_first']).casefold()]}
        yr = m['year'] or m['year_last'] or m['iso_year']
        if yr:
            result['year'] = int(yr)
    else:
        month = re.search(rf'\b({MONTH_PATTERN})\b', text, re.I)
        if month:
            result['month'] = MONTHS[month[1].casefold()]
    correction = re.search(r'\byear\s+(?:is\s+)?(\d{4})\b', text, re.I)
    if correction:
        if 'year' in result and result['year'] != int(correction[1]):
            return {'normalization_error': 'contradictory_explicit_years'}
        result['year'] = int(correction[1])
    window = re.search(r'\b(\d{1,2}:\d{2})\s*(?:to|until|[-–])\s*(\d{1,2}:\d{2})\b', text, re.I)
    if window:
        result.update(start_time=window[1], finish_time=window[2])
    else:
        for key, pattern in [('start_time', r'\b(?:from|start(?:s|ing)?(?: at)?)\s+(\d{1,2}:\d{2})\b'),
                             ('finish_time', r'\b(?:until|finish(?:es|ing)?(?: at)?|end(?:s|ing)?(?: at)?)\s+(\d{1,2}:\d{2})\b')]:
            m = re.search(pattern, text, re.I)
            if m:
                result[key] = m[1]
    return result


def resolve_calendar_date(*, day: int, month: int, year: int | None, reference_timestamp: str,
                          timezone_name: str = VENUE_TIMEZONE) -> tuple[date, dict[str, Any]]:
    reference = datetime.fromisoformat(reference_timestamp.replace('Z', '+00:00'))
    if reference.tzinfo is None:
        raise ValueError('authoritative_timestamp_requires_timezone')
    local_day = reference.astimezone(ZoneInfo(timezone_name)).date()
    if year is not None:
        resolved = date(year, month, day)  # Explicit invalid/past years never roll forward.
        source = 'client_explicit'
    else:
        resolved = None
        for candidate_year in range(local_day.year, min(local_day.year + 9, 10000)):
            try:
                candidate = date(candidate_year, month, day)
            except ValueError:
                continue  # Feb 29 advances to the next actual leap year (incl. 2100).
            if candidate >= local_day:
                resolved = candidate
                break
        if resolved is None:
            raise ValueError('invalid_calendar_day_month')
        source = 'system_inferred_next_occurrence'
    return resolved, {'year_source': source, 'reference_timestamp': reference_timestamp,
                      'timezone': timezone_name, 'explicit_client_year': year,
                      'resolved_year': resolved.year, 'rule': 'next_calendar_occurrence_v1'}


def _local_instant(day: date, clock: str, zone: ZoneInfo) -> datetime:
    local = datetime.combine(day, time.fromisoformat(clock)).replace(tzinfo=zone)
    if local.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) != local.replace(tzinfo=None):
        raise ValueError('nonexistent_local_time')
    if local.utcoffset() != local.replace(fold=1).utcoffset():
        raise ValueError('ambiguous_local_time')
    return local


def normalize_timing(value: dict[str, Any], *, reference_timestamp: str,
                     source_text: str = '', source_reference: str = '') -> dict[str, Any]:
    """Normalize component values; retain original evidence/provenance locally.

    Complete legacy ISO windows without component input retain their established
    semantics. A parsed client date never borrows a year from such a window.
    """
    components = {k: value[k] for k in ('day', 'month', 'year', 'start_time', 'finish_time') if k in value}
    if not components:
        return value
    try:
        if not components.get('day') or not components.get('month'):
            return {**components, 'date_provenance': {'year_source': 'client_explicit' if components.get('year') else 'unresolved',
                    'reference_timestamp': reference_timestamp, 'source_reference': source_reference,
                    'timezone': VENUE_TIMEZONE, 'explicit_client_year': components.get('year')}}
        resolved, provenance = resolve_calendar_date(day=int(components['day']), month=int(components['month']),
            year=int(components['year']) if components.get('year') is not None else None,
            reference_timestamp=reference_timestamp)
        provenance.update(source_reference=source_reference, client_components=dict(components))
        result = {**components, 'resolved_date': resolved.isoformat(), 'date_provenance': provenance}
        zone = ZoneInfo(VENUE_TIMEZONE)
        start = _local_instant(resolved, components['start_time'], zone) if components.get('start_time') else None
        end = _local_instant(resolved, components['finish_time'], zone) if components.get('finish_time') else None
        if start and end:
            if end <= start:
                raise ValueError('finish_must_follow_start')  # No guessed overnight duration.
            result.update(active_event_start=start.astimezone(timezone.utc).isoformat(),
                          active_event_end=end.astimezone(timezone.utc).isoformat())
        return result
    except (ValueError, TypeError, OverflowError) as exc:
        return {**components, 'normalization_error': str(exc), 'source_reference': source_reference,
                'reference_timestamp': reference_timestamp}


def missing_timing_question(messages: tuple[str, ...]) -> str:
    components: dict[str, Any] = {}
    for message in messages:
        incoming = timing_components(message)
        if incoming.get('normalization_error'):
            return 'Which event date and start and finish times would you like?'
        # A new calendar date supersedes earlier date components, but a simple
        # time-only follow-up may complete the existing partial date.
        if incoming.get('day') and incoming.get('month'):
            components = incoming
        else:
            components.update(incoming)
    missing = []
    if not components.get('day') or not components.get('month'):
        missing.append('day' if components.get('month') else 'date')
    if not components.get('start_time'):
        missing.append('start time')
    if not components.get('finish_time'):
        missing.append('finish time')
    # A complete parsed date should have been resolved by intake, not asked
    # again. Callers filter this empty result without generating a fake question.
    if not missing:
        return 'Which event date and times should I check?'  # Only for an unresolved/conflicting intake question.
    return 'What ' + (missing[0] if len(missing) == 1 else ', '.join(missing[:-1]) + ' and ' + missing[-1]) + ' would you like?'
