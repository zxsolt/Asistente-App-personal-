import httpx

from app.core.config import settings


class TelegramBotClient:
    async def send_message(self, *, chat_id: int, text: str) -> None:
        if not settings.TELEGRAM_BOT_TOKEN:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
        async with httpx.AsyncClient(
            base_url=f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}",
            timeout=20.0,
        ) as client:
            response = await client.post("/sendMessage", json={"chat_id": chat_id, "text": text})
            response.raise_for_status()
