from __future__ import annotations

from app.assistant.understanding_service import UnderstandingResult


class AssistantPolicyService:
    def choose(self, *, understanding: UnderstandingResult) -> str:
        if understanding.decision == "clarify" or understanding.missing_fields:
            return "clarify"
        if understanding.decision == "act":
            return "act"
        return "answer"
