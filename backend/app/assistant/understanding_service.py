from __future__ import annotations

from dataclasses import dataclass, field
import re

from app.assistant.date_utils import normalize_text, parse_temporal_context
from app.assistant.schemas import AssistantIntent, ParsedTemporalContext


@dataclass(slots=True)
class UnderstandingResult:
    intent: AssistantIntent
    cleaned_message: str
    decision: str
    priority: str | None
    task_type: str
    temporal: ParsedTemporalContext
    missing_fields: list[str] = field(default_factory=list)
    confidence: float = 0.0
    rationale_summary: str | None = None


class UnderstandingService:
    _TASK_QUERY_MARKERS = (
        "que tengo",
        "que tareas",
        "mis tareas",
        "tengo hoy",
        "tengo manana",
        "esta semana",
        "hoy",
        "ayer",
        "que hice",
    )
    _NOTE_QUERY_MARKERS = ("que notas", "mis notas", "ultimas notas", "notas de hoy", "notas de ayer")
    _REMINDER_QUERY_MARKERS = ("que recordatorios", "mis recordatorios", "recordatorios pendientes")
    _TASK_META_PATTERNS = {
        "quiero crear una tarea",
        "quiero crear tareas",
        "crea una tarea",
        "crear una tarea",
        "anade una tarea",
        "agrega una tarea",
        "quiero una tarea",
        "quiero crear una nueva tarea",
        "quiero crear tarea",
    }
    _NOTE_META_PATTERNS = {
        "quiero crear una nota",
        "crea una nota",
        "guarda una nota",
        "apunta una nota",
        "quiero anadir una nota",
        "quiero añadir una nota",
    }
    _REMINDER_META_PATTERNS = {
        "anademe un recordatorio",
        "añademe un recordatorio",
        "crea un recordatorio",
        "quiero un recordatorio",
        "quiero crear un recordatorio",
        "recordatorio",
    }

    def understand(self, message: str) -> UnderstandingResult:
        normalized = normalize_text(message).strip(" ?!.,")
        temporal = parse_temporal_context(message)
        priority = self._extract_priority(normalized)
        task_type = self._infer_task_type(normalized)

        if self._is_task_query(normalized):
            return UnderstandingResult(
                intent=AssistantIntent.TASK_QUERY,
                cleaned_message=message.strip(),
                decision="answer",
                priority=priority,
                task_type=task_type,
                temporal=temporal,
                confidence=0.9,
                rationale_summary="La peticion es una consulta sobre tareas ya guardadas.",
            )

        if self._is_note_query(normalized):
            return UnderstandingResult(
                intent=AssistantIntent.NOTE_QUERY,
                cleaned_message=message.strip(),
                decision="answer",
                priority=priority,
                task_type=task_type,
                temporal=temporal,
                confidence=0.88,
                rationale_summary="La peticion es una consulta sobre notas ya guardadas.",
            )

        if self._is_reminder_query(normalized):
            return UnderstandingResult(
                intent=AssistantIntent.REMINDER_QUERY,
                cleaned_message=message.strip(),
                decision="answer",
                priority=priority,
                task_type=task_type,
                temporal=temporal,
                confidence=0.88,
                rationale_summary="La peticion es una consulta sobre recordatorios guardados.",
            )

        if self._looks_like_reminder(normalized):
            cleaned = self._clean_reminder_message(message)
            missing_fields: list[str] = []
            if not cleaned:
                missing_fields.append("reminder_content")
            if temporal.due_at is None:
                missing_fields.append("when")
            return UnderstandingResult(
                intent=AssistantIntent.REMINDER_CREATE,
                cleaned_message=cleaned,
                decision="clarify" if missing_fields else "act",
                priority=priority,
                task_type=task_type,
                temporal=temporal,
                missing_fields=missing_fields,
                confidence=0.96 if not missing_fields else 0.44,
                rationale_summary=(
                    "He detectado la intencion de crear un recordatorio."
                    if not missing_fields
                    else "Se quiere crear un recordatorio, pero falta contenido o momento."
                ),
            )

        if self._looks_like_note(normalized):
            cleaned = self._clean_note_message(message)
            missing_fields = [] if cleaned else ["note_content"]
            return UnderstandingResult(
                intent=AssistantIntent.NOTE_CREATE,
                cleaned_message=cleaned,
                decision="clarify" if missing_fields else "act",
                priority=priority,
                task_type=task_type,
                temporal=temporal,
                missing_fields=missing_fields,
                confidence=0.94 if not missing_fields else 0.45,
                rationale_summary=(
                    "He detectado que quieres guardar una nota."
                    if not missing_fields
                    else "La intencion es guardar una nota, pero falta el contenido real."
                ),
            )

        if self._looks_like_week_create(normalized):
            return UnderstandingResult(
                intent=AssistantIntent.WEEK_CREATE,
                cleaned_message=message.strip(),
                decision="act",
                priority=priority,
                task_type=task_type,
                temporal=temporal,
                confidence=0.84,
                rationale_summary="La peticion es crear o abrir una nueva semana de trabajo.",
            )

        task_cleaned = self._clean_task_message(message)
        if self._looks_like_task(normalized, task_cleaned, temporal):
            missing_fields = [] if task_cleaned else ["task_content"]
            return UnderstandingResult(
                intent=AssistantIntent.TASK_CREATE,
                cleaned_message=task_cleaned,
                decision="clarify" if missing_fields else "act",
                priority=priority,
                task_type=self._infer_task_type(normalize_text(task_cleaned or normalized)),
                temporal=temporal,
                missing_fields=missing_fields,
                confidence=0.92 if not missing_fields else 0.41,
                rationale_summary=(
                    "He detectado una tarea accionable."
                    if not missing_fields
                    else "Parece que quieres crear una tarea, pero falta decir cual."
                ),
            )

        return UnderstandingResult(
            intent=AssistantIntent.GENERAL_QUERY if self._looks_like_query(normalized) else AssistantIntent.UNKNOWN,
            cleaned_message=message.strip(),
            decision="answer",
            priority=priority,
            task_type=task_type,
            temporal=temporal,
            confidence=0.55,
            rationale_summary="La peticion no encaja como alta/nota/recordatorio cerrados y pasa a respuesta abierta.",
        )

    def build_clarification(self, result: UnderstandingResult) -> str:
        if result.intent == AssistantIntent.TASK_CREATE:
            return "¿Qué tarea?"
        if result.intent == AssistantIntent.NOTE_CREATE:
            return "¿Qué nota?"
        if result.intent == AssistantIntent.REMINDER_CREATE:
            if "reminder_content" in result.missing_fields and "when" in result.missing_fields:
                return "¿De qué y para cuándo?"
            if "reminder_content" in result.missing_fields:
                return "¿Qué quieres que te recuerde?"
            return "¿Para cuándo?"
        return "¿Qué necesitas exactamente?"

    def _extract_priority(self, normalized: str) -> str | None:
        if any(token in normalized for token in ("urgente", "alta prioridad", "prioridad alta")):
            return "high"
        if "prioridad media" in normalized:
            return "medium"
        if "prioridad baja" in normalized:
            return "low"
        return None

    def _infer_task_type(self, normalized: str) -> str:
        study_keywords = ("estudiar", "curso", "leer", "repasar", "tema", "aprender", "python")
        return "study" if any(token in normalized for token in study_keywords) else "work"

    def _looks_like_query(self, normalized: str) -> bool:
        return normalized.endswith("?") or normalized.startswith(("que ", "como ", "dime ", "resume "))

    def _is_task_query(self, normalized: str) -> bool:
        return any(marker in normalized for marker in self._TASK_QUERY_MARKERS)

    def _is_note_query(self, normalized: str) -> bool:
        return any(marker in normalized for marker in self._NOTE_QUERY_MARKERS)

    def _is_reminder_query(self, normalized: str) -> bool:
        return any(marker in normalized for marker in self._REMINDER_QUERY_MARKERS)

    def _looks_like_reminder(self, normalized: str) -> bool:
        return "recuerdame" in normalized or "recordatorio" in normalized

    def _looks_like_note(self, normalized: str) -> bool:
        return "nota" in normalized or normalized.startswith(("apunta ", "guarda "))

    def _looks_like_week_create(self, normalized: str) -> bool:
        return "semana" in normalized and any(
            marker in normalized
            for marker in ("nueva semana", "crea semana", "iniciame una semana", "inicia una semana")
        )

    def _looks_like_task(self, normalized: str, cleaned: str, temporal: ParsedTemporalContext) -> bool:
        if normalized in self._TASK_META_PATTERNS:
            return True
        if "tarea" in normalized:
            return True
        if any(normalized.startswith(prefix) for prefix in ("tengo que ", "debo ", "necesito ", "quiero ")):
            return True
        if temporal.due_at or temporal.range_start:
            return bool(cleaned)
        return False

    def _clean_task_message(self, message: str) -> str:
        normalized = normalize_text(message).strip(" ?!.,")
        if normalized in self._TASK_META_PATTERNS:
            return ""

        cleaned = message.strip()
        prefixes = [
            "quiero crear una tarea",
            "quiero crear tarea",
            "crea una tarea",
            "crear una tarea",
            "anade una tarea",
            "añade una tarea",
            "agrega una tarea",
            "quiero una tarea",
            "tengo que",
            "debo",
            "necesito",
            "quiero",
            "hoy",
            "manana",
            "mañana",
            "pasado manana",
            "pasado mañana",
            "esta semana",
            "proxima semana",
            "la semana que viene",
        ]
        changed = True
        while changed:
            changed = False
            for prefix in prefixes:
                if normalize_text(cleaned).startswith(prefix):
                    cleaned = cleaned[len(prefix):].strip(" :,.-")
                    changed = True
                    break

        if cleaned.lower().startswith("hacer "):
            cleaned = cleaned[6:].strip()

        normalized_cleaned = normalize_text(cleaned).strip(" ?!.,")
        if normalized_cleaned in {
            "",
            "tarea",
            "una tarea",
            "varias tareas",
            "organizarme",
            "organizar",
            "ser productivo",
            "algo",
        }:
            return ""
        return cleaned

    def _clean_note_message(self, message: str) -> str:
        normalized = normalize_text(message).strip(" ?!.,")
        if normalized in self._NOTE_META_PATTERNS:
            return ""
        cleaned = message.strip()
        prefixes = [
            "quiero que me anadas una nota",
            "quiero que me añadas una nota",
            "quiero crear una nota",
            "quiero anadir una nota",
            "quiero añadir una nota",
            "anademe una nota",
            "añademe una nota",
            "guarda una nota",
            "apunta una nota",
            "crea una nota",
            "guarda nota",
            "apunta nota",
            "crea nota",
        ]
        for prefix in prefixes:
            if normalize_text(cleaned).startswith(prefix):
                cleaned = cleaned[len(prefix):].strip(" :,.-")
                break
        cleaned = cleaned.removeprefix("de ").removeprefix("que ").removeprefix("sobre ").strip()
        return cleaned

    def _clean_reminder_message(self, message: str) -> str:
        normalized = normalize_text(message).strip(" ?!.,")
        if normalized in self._REMINDER_META_PATTERNS:
            return ""
        cleaned = message.strip()
        prefixes = [
            "recuerdame que",
            "recuerdame",
            "recordarme",
            "crea un recordatorio",
            "crea recordatorio",
            "quiero crear un recordatorio",
            "añademe un recordatorio",
            "anademe un recordatorio",
        ]
        for prefix in prefixes:
            if normalize_text(cleaned).startswith(prefix):
                cleaned = cleaned[len(prefix):].strip(" :,.-")
                break
        cleaned = re.sub(
            r"^\s*en\s+\d+\s+(minutos|minuto|horas|hora)\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip(" :,.-")
        temporal_prefixes = ("manana", "mañana", "hoy", "pasado manana", "pasado mañana")
        for prefix in temporal_prefixes:
            if normalize_text(cleaned).startswith(prefix):
                cleaned = cleaned[len(prefix):].strip(" :,.-")
                break
        cleaned = cleaned.removeprefix("de ").strip()
        return cleaned
