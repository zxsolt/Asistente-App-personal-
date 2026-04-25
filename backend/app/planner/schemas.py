from typing import Literal

from pydantic import BaseModel, Field


class PlannerTask(BaseModel):
    title: str
    task_type: Literal["work", "study", "fitness", "personal"] = "personal"
    phase: str | None = None
    source_clause: str | None = None
    inferred: bool = False


class PlannerDay(BaseModel):
    day: str
    tasks: list[PlannerTask] = Field(default_factory=list)
    blocked: bool = False


class PlanningJson(BaseModel):
    tasks_detected: list[PlannerTask] = Field(default_factory=list)
    schedule: list[PlannerDay] = Field(default_factory=list)
    reasoning: str


class PlannerResult(BaseModel):
    natural_response: str
    planning_json: PlanningJson
    persistence_mode: Literal["draft", "applied", "none"] = "draft"
