from app.ai.client import OpenRouterClient
from app.ai.schemas import AICompletionResult


class OpenRouterService:
    def __init__(self) -> None:
        self.client = OpenRouterClient()

    async def answer(self, *, message: str, context: dict[str, object], model: str | None = None) -> AICompletionResult:
        return await self.client.complete(message=message, context=context, model=model)
