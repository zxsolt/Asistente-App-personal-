from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

from app.assistant.date_utils import normalize_text
from app.planner.context_service import PlannerContextService
from app.planner.schemas import PlannerDay, PlannerResult, PlannerTask, PlanningJson

DAY_ORDER = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
PLANNING_KEYWORDS = (
    "organiza",
    "organizame",
    "planifica",
    "reparte",
    "esta semana",
    "lunes",
    "martes",
    "miercoles",
    "jueves",
    "viernes",
    "sabado",
    "domingo",
    "terminar",
    "acabar",
    "seguir",
    "continuar",
    "no puedo",
    "descanso",
)


@dataclass(slots=True)
class ParsedClause:
    raw: str
    day: str | None
    title: str | None
    task_type: str
    blocked: bool = False
    continuity: bool = False


class PlannerService:
    def __init__(self, db) -> None:
        self.db = db
        self.context_service = PlannerContextService(db)

    def should_plan(self, *, message: str) -> bool:
        normalized = normalize_text(message)
        if any(keyword in normalized for keyword in PLANNING_KEYWORDS):
            return True
        if sum(1 for day in DAY_ORDER if day in normalized) >= 2:
            return True
        if ":" in message and any(token in normalized for token in ("tareas", "plan", "organiza")):
            return True
        return False

    def _split_clauses(self, message: str) -> list[str]:
        source = message.replace("\n", ",")
        source = re.sub(r"\s+y\s+el\s+", ", el ", source, flags=re.IGNORECASE)
        source = re.sub(r"\s+y\s+la\s+", ", la ", source, flags=re.IGNORECASE)
        parts = [part.strip() for part in re.split(r"[;,]", source) if part.strip()]
        return parts or [message.strip()]

    def _extract_day(self, normalized_clause: str) -> str | None:
        for day in DAY_ORDER:
            if day in normalized_clause:
                return day
        if "manana" in normalized_clause:
            return "manana"
        if "pasado manana" in normalized_clause:
            return "pasado manana"
        return None

    def _infer_type(self, normalized_clause: str) -> str:
        if any(token in normalized_clause for token in ("estudi", "mates", "curso", "repasar", "leer")):
            return "study"
        if any(token in normalized_clause for token in ("gym", "gim", "entreno", "fitness", "correr")):
            return "fitness"
        if any(token in normalized_clause for token in ("famil", "casa", "compr", "padre", "madre")):
            return "personal"
        return "work"

    def _clean_clause_title(self, clause: str) -> str:
        cleaned = clause.strip()
        patterns = [
            r"^(este|esta|el|la)\s+",
            r"^(lunes|martes|miercoles|jueves|viernes|sabado|domingo)\s+",
            r"^(voy a|quiero|tengo que|debo|me gustaria|me gustaría)\s+",
            r"^(hacer|hacer la tarea de|hacer la tarea|estudiar|terminar de|terminar|seguir con|continuar con|empezar)\s+",
            r"^(quiero que me anadas|quiero que me añadas|anademe|añademe|anade|añade)\s+",
            r"^(una|varias|estas)\s+tareas?\s*:?\s*",
        ]
        changed = True
        while changed:
            changed = False
            for pattern in patterns:
                next_cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
                if next_cleaned != cleaned:
                    cleaned = next_cleaned
                    changed = True
        return cleaned.strip(" .:-")

    def _parse_clause(self, clause: str) -> ParsedClause:
        normalized = normalize_text(clause)
        blocked = any(token in normalized for token in ("no puedo", "descanso", "libre"))
        continuity = any(token in normalized for token in ("terminar", "acabar", "seguir", "continuar"))
        title = None if blocked else self._clean_clause_title(clause)
        return ParsedClause(
            raw=clause,
            day=self._extract_day(normalized),
            title=title or None,
            task_type=self._infer_type(normalized),
            blocked=blocked,
            continuity=continuity,
        )

    def _find_relevant_previous_task(self, *, task_type: str, context: dict[str, object]) -> str | None:
        relevant_entities = context.get("relevant_entities", {})
        tasks = relevant_entities.get("tasks", []) if isinstance(relevant_entities, dict) else []
        for task in tasks:
            if task.get("task_type") == task_type:
                return task.get("name")

        active_context = context.get("active_context", {})
        active_tasks = active_context.get("active_tasks", []) if isinstance(active_context, dict) else []
        for task in active_tasks:
            if task.get("task_type") == task_type:
                return task.get("name")
        return None

    def _allocate_day(self, *, explicit_day: str | None, blocked_days: set[str], load_by_day: dict[str, int]) -> str:
        if explicit_day and explicit_day in DAY_ORDER:
            return explicit_day

        candidates = [day for day in DAY_ORDER[:5] if day not in blocked_days]
        if not candidates:
            candidates = [day for day in DAY_ORDER if day not in blocked_days] or DAY_ORDER[:]
        return min(candidates, key=lambda day: (load_by_day[day], DAY_ORDER.index(day)))

    async def build_plan(self, *, user_id: int, message: str) -> PlannerResult:
        context = await self.context_service.build_prioritized_context(user_id=user_id, query=message)
        clauses = [self._parse_clause(clause) for clause in self._split_clauses(message)]

        blocked_days = {clause.day for clause in clauses if clause.blocked and clause.day in DAY_ORDER}
        load_by_day: dict[str, int] = defaultdict(int)
        schedule_map: dict[str, list[PlannerTask]] = {day: [] for day in DAY_ORDER}
        tasks_detected: list[PlannerTask] = []
        reasoning_steps: list[str] = []

        for clause in clauses:
            if clause.blocked:
                if clause.day:
                    reasoning_steps.append(f"Bloqueo {clause.day} por restriccion explicita del usuario.")
                continue

            if not clause.title:
                continue

            task = PlannerTask(
                title=clause.title,
                task_type=clause.task_type,  # type: ignore[arg-type]
                phase="final" if clause.continuity else "normal",
                source_clause=clause.raw,
                inferred=False,
            )
            tasks_detected.append(task)
            assigned_day = self._allocate_day(
                explicit_day=clause.day if clause.day in DAY_ORDER else None,
                blocked_days=blocked_days,
                load_by_day=load_by_day,
            )
            schedule_map[assigned_day].append(task)
            load_by_day[assigned_day] += 1

            if clause.day in DAY_ORDER:
                reasoning_steps.append(f"Respeto el dia explicito {clause.day} para {clause.title}.")

            if clause.continuity:
                previous_name = self._find_relevant_previous_task(task_type=clause.task_type, context=context) or clause.title
                previous_index = max(0, DAY_ORDER.index(assigned_day) - 1)
                previous_day = DAY_ORDER[previous_index]
                if previous_day not in blocked_days and previous_day != assigned_day:
                    prep_task = PlannerTask(
                        title=f"Avance previo de {previous_name}",
                        task_type=clause.task_type,  # type: ignore[arg-type]
                        phase="preparacion",
                        source_clause=clause.raw,
                        inferred=True,
                    )
                    schedule_map[previous_day].append(prep_task)
                    load_by_day[previous_day] += 1
                    tasks_detected.append(prep_task)
                    reasoning_steps.append(
                        f"Anado una sesion previa el {previous_day} para que {clause.title} tenga continuidad coherente."
                    )

        if not tasks_detected:
            reasoning = (
                "No hay suficiente detalle para repartir tareas automaticamente, asi que devuelvo un borrador vacio."
            )
            return PlannerResult(
                natural_response=(
                    "Puedo proponerte un plan, pero necesito mas detalle. "
                    "Enviame tareas concretas y, si quieres, dias o restricciones."
                ),
                planning_json=PlanningJson(tasks_detected=[], schedule=[], reasoning=reasoning),
                persistence_mode="draft",
            )

        schedule = [
            PlannerDay(day=day, tasks=schedule_map[day], blocked=day in blocked_days)
            for day in DAY_ORDER
            if schedule_map[day] or day in blocked_days
        ]

        reasoning = " ".join(reasoning_steps) or (
            "Distribuyo la carga de forma equilibrada y priorizo los dias mencionados por el usuario."
        )
        summary_lines = ["He preparado un borrador de plan semanal:"]
        for day in schedule:
            if day.blocked:
                summary_lines.append(f"- {day.day}: bloqueado")
                continue
            task_names = ", ".join(task.title for task in day.tasks)
            summary_lines.append(f"- {day.day}: {task_names}")

        return PlannerResult(
            natural_response="\n".join(summary_lines),
            planning_json=PlanningJson(
                tasks_detected=tasks_detected,
                schedule=schedule,
                reasoning=reasoning,
            ),
            persistence_mode="draft",
        )
