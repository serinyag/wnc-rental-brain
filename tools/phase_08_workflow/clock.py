from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Protocol


class Clock(Protocol):
    def now(self) -> str: ...


def parse_timestamp(value: str) -> datetime:
    normalized = value.strip()
    if not normalized:
        raise ValueError("timestamp value must not be blank")
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def format_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class SystemClock:
    def now(self) -> str:
        return format_timestamp(datetime.now(timezone.utc))


@dataclass(frozen=True)
class CallableClock:
    callback: Callable[[], str]

    def now(self) -> str:
        return self.callback()


@dataclass
class MutableTestClock:
    system_clock: Clock = field(default_factory=SystemClock)
    _current_time: str | None = None

    def now(self) -> str:
        return self._current_time or self.system_clock.now()

    def is_simulated(self) -> bool:
        return self._current_time is not None

    def real_time(self) -> str:
        return self.system_clock.now()

    def set(self, timestamp_value: str) -> str:
        self._current_time = format_timestamp(parse_timestamp(timestamp_value))
        return self._current_time

    def advance(self, *, hours: int = 0, days: int = 0) -> str:
        if hours == 0 and days == 0:
            raise ValueError("clock advance requires a non-zero offset")
        self._current_time = format_timestamp(
            parse_timestamp(self.now()) + timedelta(hours=hours, days=days)
        )
        return self._current_time

    def reset(self) -> str:
        self._current_time = None
        return self.real_time()
