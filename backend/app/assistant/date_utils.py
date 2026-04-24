from datetime import date, datetime, time, timedelta, timezone
import re
import unicodedata

from app.assistant.schemas import ParsedTemporalContext

WEEKDAY_MAP = {
    "lunes": 0,
    "martes": 1,
    "miercoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sabado": 5,
    "domingo": 6,
}


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.lower())
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def start_of_week(day: date) -> date:
    return day - timedelta(days=day.weekday())


def end_of_week(day: date) -> date:
    return start_of_week(day) + timedelta(days=6)


def combine_day(day: date) -> datetime:
    return datetime.combine(day, time(hour=9, tzinfo=timezone.utc))


def next_weekday(day: date, weekday: int) -> date:
    delta = (weekday - day.weekday()) % 7
    if delta == 0:
        delta = 7
    return day + timedelta(days=delta)


def parse_temporal_context(message: str, now: datetime | None = None) -> ParsedTemporalContext:
    current = now or datetime.now(timezone.utc)
    today = current.date()
    normalized = normalize_text(message)

    if "pasado manana" in normalized:
        target = today + timedelta(days=2)
        return ParsedTemporalContext(due_at=combine_day(target), range_start=target, range_end=target, matched_phrase="pasado manana")
    if "manana" in normalized:
        target = today + timedelta(days=1)
        return ParsedTemporalContext(due_at=combine_day(target), range_start=target, range_end=target, matched_phrase="manana")
    if "hoy" in normalized:
        return ParsedTemporalContext(due_at=combine_day(today), range_start=today, range_end=today, matched_phrase="hoy")
    if "ayer" in normalized:
        target = today - timedelta(days=1)
        return ParsedTemporalContext(range_start=target, range_end=target, matched_phrase="ayer")
    if "esta semana" in normalized:
        return ParsedTemporalContext(range_start=start_of_week(today), range_end=end_of_week(today), matched_phrase="esta semana")
    if "proxima semana" in normalized or "la semana que viene" in normalized:
        start = start_of_week(today) + timedelta(days=7)
        return ParsedTemporalContext(range_start=start, range_end=start + timedelta(days=6), matched_phrase="proxima semana")

    weekday_pattern = re.compile(r"\b(lunes|martes|miercoles|jueves|viernes|sabado|domingo)\b")
    match = weekday_pattern.search(normalized)
    if match:
        target = next_weekday(today, WEEKDAY_MAP[match.group(1)])
        return ParsedTemporalContext(due_at=combine_day(target), range_start=target, range_end=target, matched_phrase=match.group(1))

    return ParsedTemporalContext()
