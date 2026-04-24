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


def _clean_prefixes(message: str) -> str:
    cleaned = message.strip()
    normalized = normalize_text(cleaned)
    token_prefixes = [
        "crea tarea",
        "crear tarea",
        "anade tarea",
        "agrega tarea",
        "pon tarea",
        "apunta tarea",
        "recuerdame que",
        "recuerdame",
        "recordarme",
        "apunta nota",
        "guarda nota",
        "crea nota",
        "anade nota",
        "que",
    ]
    original_tokens = cleaned.split()
    for prefix in token_prefixes:
        if normalized.startswith(prefix):
            prefix_len = len(prefix.split())
            cleaned = " ".join(original_tokens[prefix_len:]).lstrip(": ").strip()
            break
    return cleaned


def classify_message(message: str) -> IntentResult:
    normalized = normalize_text(message)
    priority = _extract_priority(message)
    task_type = _infer_task_type(message)

    note_markers = ("nota", "apunta", "guardar nota", "guarda nota")
    reminder_markers = ("recuerdame", "recordarme", "recordatorio")
    query_markers = ("que tengo", "que hice", "tengo hoy", "esta semana", "hoy", "ayer")
    task_markers = ("tarea", "pendiente", "haz", "hacer", "crear")

    if any(marker in normalized for marker in note_markers) and "nota" in normalized:
        intent = AssistantIntent.NOTE_CREATE
    elif any(marker in normalized for marker in reminder_markers):
        intent = AssistantIntent.REMINDER_CREATE
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
        cleaned_message=_clean_prefixes(message),
        priority=priority,
        task_type=task_type,
    )
