"""Topic structure is validated separately from whether the evidence supports it."""

from typing import Annotated, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


SourceID = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
RecordID = Annotated[str, Field(pattern=r"^[a-f0-9]{32}$")]


class EvidenceReference(BaseModel):
    """A short quotation located in one extracted source block."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    document_id: SourceID
    filename: str = Field(min_length=1, max_length=255)
    location: str = Field(min_length=1, max_length=300)
    excerpt: str = Field(min_length=1, max_length=3000)


class TopicCandidate(BaseModel):
    """A readable candidate; local source-aware checks provide review guidance."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=120)
    core_insight: str = Field(min_length=1, max_length=500)
    context: str = Field(min_length=1, max_length=1200)
    target_audience: str = Field(min_length=1, max_length=300)
    suggested_format: str = Field(min_length=1, max_length=300)
    sources: list[EvidenceReference] = Field(max_length=10)

    @field_validator("sources")
    @classmethod
    def unique_evidence(cls, value: list[EvidenceReference]) -> list[EvidenceReference]:
        keys = [(item.document_id, item.location, item.excerpt) for item in value]
        if len(keys) != len(set(keys)):
            raise ValueError("A topic must not repeat the same evidence reference.")
        return value


class TopicIdea(TopicCandidate):
    """An accepted topic with a stable application-owned identifier."""

    topic_id: RecordID = Field(default_factory=lambda: uuid4().hex)
    origin: Literal["generated", "sample"] = "generated"
