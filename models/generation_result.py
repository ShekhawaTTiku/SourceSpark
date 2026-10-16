"""The provider returns a bounded candidate batch, never a complete workspace."""

from pydantic import BaseModel, ConfigDict, Field

from models.topic import TopicCandidate


class GenerationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    candidates: list[TopicCandidate] = Field(max_length=10)
    sufficiency_note: str = Field(min_length=1, max_length=1000)
