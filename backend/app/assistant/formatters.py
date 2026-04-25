from collections.abc import Sequence

from app.models.full_task import FullTask
from app.models.note import Note
from app.models.reminder import Reminder
from app.models.week import Week


def format_task_confirmation(task: FullTask) -> str:
    parts = [f"Tarea creada: {task.name}"]
    if task.due_at:
        parts.append(f"para {task.due_at.date().isoformat()}")
    if task.priority:
        parts.append(f"prioridad {task.priority}")
    return " | ".join(parts)


def format_multi_task_confirmation(tasks: Sequence[FullTask]) -> str:
    if not tasks:
        return "No he podido crear tareas."
    lines = ["Tareas creadas:"]
    for task in tasks[:10]:
        lines.append(f"- {task.name}")
    return "\n".join(lines)


def format_task_list(tasks: Sequence[FullTask], *, heading: str) -> str:
    if not tasks:
        return f"{heading}: no tienes tareas registradas."
    lines = [f"{heading}:"]
    for task in tasks[:10]:
        status = "completada" if task.completed else "pendiente"
        due = f" ({task.due_at.date().isoformat()})" if task.due_at else ""
        lines.append(f"- {task.name}{due} [{status}]")
    return "\n".join(lines)


def format_note_confirmation(note: Note) -> str:
    return f"Nota guardada en categoria {note.category}: {note.content}"


def format_reminder_confirmation(reminder: Reminder) -> str:
    return f"Recordatorio creado: {reminder.title} para {reminder.scheduled_for.isoformat()}"


def format_week_confirmation(week: Week) -> str:
    return f"Semana creada: {week.start_date.isoformat()} -> {week.end_date.isoformat()}"
