from collections.abc import Mapping


def build_assistant_system_prompt() -> str:
    return (
        "Eres un asistente personal preciso y conciso. "
        "Usa solo el contexto proporcionado. "
        "Si el contexto no basta, dilo claramente. "
        "No inventes tareas, notas o recordatorios inexistentes."
    )


def build_assistant_user_prompt(message: str, context: Mapping[str, object]) -> str:
    return (
        "Consulta del usuario:\n"
        f"{message.strip()}\n\n"
        "Contexto disponible:\n"
        f"{context!r}\n\n"
        "Responde en espanol, de forma breve y accionable."
    )
