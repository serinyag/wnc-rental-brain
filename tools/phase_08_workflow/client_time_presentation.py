"""Finite scoped email presentation; never change canonical timing or authority."""
from collections import OrderedDict
from datetime import datetime
from zoneinfo import ZoneInfo
import re


def scoped_parts(value):
    scope = value.get('scope', {})
    try:
        start, end = (datetime.fromisoformat(scope[k]) for k in ('start', 'end'))
        if start.tzinfo is None or end.tzinfo is None or start >= end:
            return None
        start, end = (t.astimezone(ZoneInfo('Europe/Amsterdam')) for t in (start, end))
        end_label = end.strftime('%H:%M') if start.date() == end.date() else end.strftime('%d %B %Y %H:%M')
        interval = f'{start.day} {start:%B %Y} from {start:%H:%M} to {end_label}'
        assertion = value['assertion'].replace(' (Europe/Amsterdam)', '')
        suffix = ' for ' + interval + '.'
        if not assertion.endswith(suffix):
            return None
        return 'For ' + interval + ':', assertion[:-len(suffix)] + '.'
    except (KeyError, TypeError, ValueError):
        return None


def confirmation_blocks(values):
    values = tuple(values)
    if len(values) == 1:
        return (values[0]["assertion"],)
    groups = OrderedDict()
    for value in values:
        parts = scoped_parts(value)
        if parts is None:
            groups.setdefault(None, []).append(value['assertion'])
        else:
            groups.setdefault(parts[0], []).append(parts[1])
    return tuple('\n'.join(rows) if header is None else header + '\n' + '\n'.join('- ' + row for row in rows)
                 for header, rows in groups.items())


def confirmation_witness(value, body):
    """Accept only a complete exact assertion or exact bullet under its own scope.

    A matching date elsewhere in the email cannot authorize an unscoped claim.
    Unknown/expanded bullets are left in the body for normal safety validation.
    """
    assertion = value['assertion']
    if assertion.casefold() in body.casefold():
        return assertion
    parts = scoped_parts(value)
    if parts is None:
        return None
    header, short = parts
    for match in re.finditer(r'^' + re.escape(header) + r'\n((?:- [^\n]+(?:\n|$))+)', body, re.I | re.M):
        for line in match.group(1).splitlines():
            if line.casefold() == ('- ' + short).casefold():
                return line
    return None
