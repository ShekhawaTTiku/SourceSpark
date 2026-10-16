"""One active plan selects reusable topics and records explicit finalization."""

from datetime import date, datetime, timedelta
from typing import Literal, Self
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from models.topic import RecordID


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    plan_id: RecordID = Field(default_factory=lambda: uuid4().hex)
    name: str = Field(default="Untitled plan", min_length=1, max_length=200)
    mode: Literal["Week", "Campaign"] = "Week"
    weekly_days: Literal[5, 7] = 5
    target: int | None = Field(default=None, strict=True, ge=1)
    audience: str = Field(default="", max_length=500)
    goal: str = Field(default="", max_length=2000)
    guidance: str = Field(default="", max_length=4000)
    selected_topic_ids: list[RecordID] = Field(default_factory=list)
    day_assignments: dict[int, RecordID] = Field(default_factory=dict)
    start_date: date | None = None
    status: Literal["DRAFT", "READY_FOR_REVIEW", "FINALIZED"] = "DRAFT"
    shortfall_acknowledged: bool = Field(default=False, strict=True)
    finalized_at: datetime | None = None

    @field_validator("start_date", mode="before")
    @classmethod
    def calendar_date_type(cls, value: object) -> object:
        if value is not None and type(value) not in {date, str}:
            raise ValueError("The optional start date must be a calendar date.")
        return value

    @property
    def effective_target(self) -> int | None:
        return self.weekly_days if self.mode == "Week" else self.target

    @property
    def remaining_slots(self) -> int | None:
        if self.effective_target is None:
            return None
        return max(0, self.effective_target - len(self.selected_topic_ids))

    @model_validator(mode="after")
    def consistent_plan(self) -> Self:
        selected = self.selected_topic_ids
        if len(selected) != len(set(selected)):
            raise ValueError("Plan selections must be unique.")
        if self.mode == "Week":
            if self.target is not None:
                raise ValueError("Weekly targets come from the five/seven day setting.")
            if any(day < 0 or day >= self.weekly_days for day in self.day_assignments):
                raise ValueError("Weekly assignments must use valid day slots.")
            ordered = [self.day_assignments[day] for day in sorted(self.day_assignments)]
            if ordered != selected:
                raise ValueError("Weekly selections must match assignments in day order.")
            if self.start_date is not None and self.start_date.weekday() != 0:
                raise ValueError("The optional week-start date must be a Monday.")
            if self.start_date is not None:
                try:
                    self.start_date + timedelta(days=self.weekly_days - 1)
                except OverflowError:
                    raise ValueError("The entire week must fit within the supported calendar.") from None
        elif self.day_assignments or self.start_date is not None:
            raise ValueError("Campaigns do not use weekly assignments or a start date.")
        if self.effective_target is not None and len(selected) > self.effective_target:
            raise ValueError("Selections exceed the active plan target.")
        ready = bool(selected) and (
            self.effective_target is None or len(selected) == self.effective_target
        )
        if self.status == "FINALIZED":
            if not selected:
                raise ValueError("An empty plan cannot be finalized.")
            if self.finalized_at is None:
                raise ValueError("A finalized plan requires its finalization time.")
            if self.remaining_slots and not self.shortfall_acknowledged:
                raise ValueError("Finalizing a shorter plan requires acknowledgement.")
        else:
            expected = "READY_FOR_REVIEW" if ready else "DRAFT"
            if self.status != expected:
                raise ValueError("Plan readiness does not match its selections and target.")
            if self.finalized_at is not None or self.shortfall_acknowledged:
                raise ValueError("Draft plans cannot retain finalization metadata.")
        return self
