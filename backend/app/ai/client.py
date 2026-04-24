import httpx

from app.ai.schemas import AICompletionResult
from app.core.config import settings


class OpenRouterClient:
    async def complete(self, *, message: str, context: dict[str, object], model: str | None = None) -> AICompletionResult:
        if not settings.OPENROUTER_API_KEY:
            raise RuntimeError("OPENROUTER_API_KEY is not configured")

        payload = {
            "model": model or settings.OPENROUTER_DEFAULT_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente personal preciso y conciso. "
                        "Usa solo el contexto proporcionado. "
                        "No inventes datos."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Consulta:\n{message.strip()}\n\n"
                        f"Contexto:\n{context!r}\n\n"
                        "Responde en espanol de forma breve."
                    ),
                },
            ],
        }
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.OPENROUTER_SITE_URL,
            "X-Title": settings.OPENROUTER_APP_NAME,
        }
        async with httpx.AsyncClient(base_url=settings.OPENROUTER_BASE_URL, timeout=30.0) as client:
            response = await client.post("/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        return AICompletionResult(text=text.strip(), model=payload["model"])
