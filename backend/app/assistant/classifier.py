import re
from dataclasses import dataclass

from app.assistant.date_utils import normalize_text
from app.assistant.schemas import AssistantIntent


@dataclass(slots=True)
class IntentResult:
    intent: AssistantIntent
    cleaned_message: str
    priority: str | None
    task_type: str


def _extract_priority(message: str) -> str | None:
    normalized = normalize_text(message)
    if any(token in normalized for token in ("urgente", "alta prioridad", "prioridad alta")):
        return "high"
    if "prioridad media" in normalized:
        return "medium"
    if "prioridad baja" in normalized:
        return "low"
    return None


def _infer_task_type(message: str) -> str:
    normalized = normalize_text(message)
    study_keywords = ("estudiar", "curso", "leer", "repasar", "tema", "aprender")
    return "study" if any(token in normalized for token in study_keywords) else "work"


def _tokenize(message: str) -> tuple[list[str], list[str]]:
    original_tokens = message.strip().split()
    normalized_tokens = [normalize_text(token).strip(",:;.?!") for token in original_tokens]
    return original_tokens, normalized_tokens


def _strip_prefix(message: str, prefixes: list[list[str]], *, drop_leading: tuple[str, ...] = ()) -> str:
    original_tokens, normalized_tokens = _tokenize(message)

    for prefix in prefixes:
        if normalized_tokens[: len(prefix)] == prefix:
            remaining = original_tokens[len(prefix):]
            while remaining and normalize_text(remaining[0]).strip(",:;.?!") in drop_leading:
                remaining = remaining[1:]
            return " ".join(remaining).strip(" :,-")

    return message.strip()


def _clean_message_for_intent(message: str, intent: AssistantIntent) -> str:
    if intent == AssistantIntent.NOTE_CREATE:
        return _strip_prefix(
            message,
            [
                ["quiero", "que", "me", "anadas", "una", "nota"],
                ["quiero", "anadir", "una", "nota"],
                ["anademe", "una", "nota"],
                ["anade", "una", "nota"],
                ["guarda", "una", "nota"],
                ["apunta", "una", "nota"],
                ["crea", "una", "nota"],
                ["anade", "nota"],
                ["guarda", "nota"],
                ["apunta", "nota"],
                ["crea", "nota"],
            ],
            drop_leading=("de", "que", "sobre"),
        )

    if intent == AssistantIntent.TASK_CREATE:
        return _strip_prefix(
            message,
            [
                ["quiero", "que", "me", "anadas", "una", "tarea"],
                ["quiero", "crear", "una", "tarea"],
                ["crea", "una", "tarea"],
                ["crear", "una", "tarea"],
                ["anade", "una", "tarea"],
                ["agrega", "una", "tarea"],
                ["pon", "una", "tarea"],
                ["apunta", "una", "tarea"],
                ["crea", "tarea"],
                ["crear", "tarea"],
                ["anade", "tarea"],
                ["agrega", "tarea"],
                ["pon", "tarea"],
                ["apunta", "tarea"],
            ],
            drop_leading=("de",),
        )

    if intent == AssistantIntent.REMINDER_CREATE:
        return _strip_prefix(
            message,
            [
                ["recuerdame", "que"],
                ["recuerdame"],
                ["recordarme"],
                ["crea", "recordatorio"],
                ["crea", "un", "recordatorio"],
            ],
            drop_leading=("de",),
        )

    return message.strip()


def classify_message(message: str) -> IntentResult:
    normalized = normalize_text(message)
    priority = _extract_priority(message)
    task_type = _infer_task_type(message)

    note_markers = ("nota", "apunta", "guardar nota", "guarda nota")
    reminder_markers = ("recuerdame", "recordarme", "recordatorio")
    query_markers = ("que tengo", "que hice", "tengo hoy", "esta semana", "hoy", "ayer")
    week_markers = ("nueva semana", "nueva semana", "inicia semana", "iniciame una semana", "crea semana", "crear semana")
    task_markers = ("tarea", "pendiente", "haz", "hacer", "crear")

    if any(marker in normalized for marker in note_markers) and "nota" in normalized:
        intent = AssistantIntent.NOTE_CREATE
    elif any(marker in normalized for marker in reminder_markers):
        intent = AssistantIntent.REMINDER_CREATE
    elif "semana" in normalized and any(marker in normalized for marker in week_markers):
        intent = AssistantIntent.WEEK_CREATE
    elif any(marker in normalized for marker in query_markers) and "nota" not in normalized:
        intent = AssistantIntent.TASK_QUERY
    elif "tarea" in normalized or any(normalized.startswith(token) for token in task_markers):
        intent = AssistantIntent.TASK_CREATE
    elif normalized.endswith("?") or normalized.startswith(("como ", "resume", "resumen", "dime ")):
        intent = AssistantIntent.GENERAL_QUERY
    else:
        intent = AssistantIntent.UNKNOWN

    return IntentResult(
        intent=intent,
        cleaned_message=_clean_message_for_intent(message, intent),
        priority=priority,
        task_type=task_type,
    )
