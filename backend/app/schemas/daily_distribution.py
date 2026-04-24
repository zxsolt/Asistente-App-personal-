from typing import Literal

from pydantic import BaseModel

DayLiteral = Literal["monday", "tuesday", "wednesday", "thursday", "friday", "saturday_morning", "saturday_afternoon", "sunday_morning", "sunday_afternoon"]


class DailyDistributionUpsert(BaseModel):
    day: DayLiteral
    day_type: str | None = None  # work / study / rest
    task_assignments: list[str] = []


class DailyDistributionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    week_id: int
    day: str
    day_type: str | None
    task_assignments: str | None  # stored as comma-separated

    def assignments_list(self) -> list[str]:
        if not self.task_assignments:
            return []
        return [t.strip() for t in self.task_assignments.split(",") if t.strip()]
