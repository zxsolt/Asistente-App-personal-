from dataclasses import dataclass


@dataclass(slots=True)
class AICompletionResult:
    text: str
    model: str
    provider: str = "openrouter"
