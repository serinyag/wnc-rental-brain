"""Present explicit client details without filling gaps or granting authority."""
from datetime import datetime
from zoneinfo import ZoneInfo

TECHNICAL_LABELS = {
    'projection_display': 'Projection', 'microphones': 'Microphones',
    'audio_playback': 'Audio playback', 'dj_sound_booth': 'DJ sound booth',
    'internet_connectivity': 'Internet connection', 'livestream_recording': 'Live streaming',
    'other_technical': 'Other technical equipment',
}


def technical_details(value):
    if not isinstance(value, dict) or not value:
        return {}
    if any(k not in TECHNICAL_LABELS or not isinstance(v, str) or not v.strip()
           or len(v) > 500 or '\n' in v or '\r' in v for k, v in value.items()):
        raise ValueError('invalid_technical_request_details')
    return {k: v.strip() for k, v in value.items()}


def technical_summary(requirements, details):
    subjects = list(dict.fromkeys([*(requirements if isinstance(requirements, list) else []), *details]))
    return '; '.join(TECHNICAL_LABELS.get(k, k.replace('_', ' ')) + (': ' + details[k] if k in details else '') for k in subjects)


def event_timing(start, end, schedule=None):
    """Complete active interval wins; partial requests remain separate evidence."""
    def local(v):
        if not v: return None
        parsed = datetime.fromisoformat(v.replace('Z', '+00:00'))
        if parsed.tzinfo is None: raise ValueError('event_interval_timezone_required')
        return parsed.astimezone(ZoneInfo('Europe/Amsterdam'))
    first, last = local(start), local(end)
    raw = schedule if isinstance(schedule, dict) else {}
    date = first.date().isoformat() if first else raw.get('date')
    start_time = first.strftime('%H:%M') if first else raw.get('start') or raw.get('time')
    end_time = last.strftime('%H:%M') if last else raw.get('end')
    rows, missing = [], []
    if date:
        day = datetime.fromisoformat(date)
        label = f'{day.day} {day:%B %Y}'
        if last and last.date().isoformat() != date: label += f'–{last.day} {last:%B %Y}'
        rows.append('Date: ' + label)
    else: missing.append('Event date')
    if start_time and end_time:
        rows.append('Time: ' + str(start_time) + '–' + str(end_time))
    else:
        if start_time: rows.append('Start time: ' + str(start_time))
        else: missing.append('Event start time')
        if end_time: rows.append('End time: ' + str(end_time))
        else: missing.append('Event end time')
    if raw.get('approximate'): rows.append('Approximate timing requested: ' + str(raw['approximate']))
    if first and raw.get('date') and raw['date'] != first.date().isoformat():
        day = datetime.fromisoformat(raw['date'])
        rows.append(f'Additional requested schedule date: {day.day} {day:%B %Y} (requires review)')
    for component, supplied, active in (('start', raw.get('start') or raw.get('time'), first), ('end', raw.get('end'), last)):
        if active and supplied and supplied != active.strftime('%H:%M'):
            rows.append('Additional requested ' + component + ' time: ' + str(supplied) + ' (requires review)')
    if raw.get('dates'):
        extra = [d for d in raw['dates'] if d != date]
        if extra:
            rows.append('Additional requested event dates: ' + ', '.join(datetime.fromisoformat(d).strftime('%d %B %Y') for d in extra))
    if raw.get('timezone') not in {None, 'Europe/Amsterdam'} and not first:
        rows.append('Requested timezone: ' + str(raw['timezone']))
    return rows, missing
