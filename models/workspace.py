"""Reusable source/topic library with validated cross-record relationships."""

from datetime import datetime, timezone
from pathlib import PurePosixPath, PureWindowsPath
import re
from typing import Literal, Self
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from config.settings import MAX_CAMPAIGN_BYTES, MAX_CONTEXT_CHARACTERS, MAX_DOCUMENTS, MAX_FILE_BYTES
from models.plan import Plan
from models.topic import RecordID, SourceID, TopicIdea


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DocumentRecord(BaseModel):
    """Extracted text and provenance; the original binary upload is not retained."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    document_id: SourceID
    filename: str = Field(min_length=1, max_length=255)
    file_type: Literal["pdf", "docx", "xlsx", "csv"]
    size_bytes: int = Field(strict=True, ge=1, le=MAX_FILE_BYTES)
    content: str = Field(min_length=1, max_length=MAX_CONTEXT_CHARACTERS)
    locations: dict[str, str] = Field(min_length=1, max_length=10_000)
    warnings: list[str] = Field(default_factory=list, max_length=1000)
    participated: bool = Field(default=False, strict=True)

    @property
    def character_count(self) -> int:
        return len(self.content)

    @property
    def content_characters(self) -> int:
        """Compatibility name used by the source inspector."""
        return len(self.content)

    @field_validator("filename")
    @classmethod
    def safe_filename(cls, value: str) -> str:
        if (PureWindowsPath(value).name != value or PurePosixPath(value).name != value
                or value in {".", ".."} or re.search(r'[<>:"|?*\x00-\x1f]', value)
                or value.endswith((".", " "))):
            raise ValueError("A source filename must be a plain basename without a path.")
        return value

    @model_validator(mode="after")
    def consistent_extraction(self) -> Self:
        if self.filename.rsplit(".", 1)[-1].lower() != self.file_type:
            raise ValueError("Source filename and file type disagree.")
        for location, text in self.locations.items():
            if not location.strip() or len(location) > 300:
                raise ValueError("Every source location needs a short nonempty label.")
            if not text.strip() or len(text) > MAX_CONTEXT_CHARACTERS:
                raise ValueError("Every source location needs readable bounded text.")
        expected = "\n\n".join(f"[{location}]\n{text}" for location, text in self.locations.items())
        if self.content != expected:
            raise ValueError("Extracted content must exactly match its source locations.")
        if any(not warning.strip() or len(warning) > 2000 for warning in self.warnings):
            raise ValueError("Source warnings must be nonempty and bounded.")
        return self


class Workspace(BaseModel):
    """All durable working data; provider credentials never belong in this model."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    workspace_id: RecordID = Field(default_factory=lambda: uuid4().hex)
    name: str = Field(default="Untitled workspace", min_length=1, max_length=200)
    documents: list[DocumentRecord] = Field(default_factory=list, max_length=MAX_DOCUMENTS)
    topics: list[TopicIdea] = Field(default_factory=list)
    excluded_topic_ids: list[RecordID] = Field(default_factory=list)
    plan: Plan = Field(default_factory=Plan)
    busy: bool = Field(default=False, strict=True)
    pool_revision: int = Field(default=0, strict=True, ge=0)
    request_round: int = Field(default=0, strict=True, ge=0)
    last_successful_request: str | None = Field(default=None, max_length=200)
    sufficiency_note: str = Field(default="", max_length=1000)
    feedback: list[str] = Field(default_factory=list, max_length=1000)
    created_at: datetime = Field(default_factory=utc_now)
    modified_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def consistent_workspace(self) -> Self:
        documents = {item.document_id: item for item in self.documents}
        topics = {item.topic_id: item for item in self.topics}
        if len(documents) != len(self.documents):
            raise ValueError("Source identifiers must be unique.")
        if len({item.filename.casefold() for item in self.documents}) != len(self.documents):
            raise ValueError("Source filenames must be unique ignoring case.")
        if sum(item.size_bytes for item in self.documents) > MAX_CAMPAIGN_BYTES:
            raise ValueError("The source library exceeds the permitted total upload size.")
        if len(topics) != len(self.topics):
            raise ValueError("Topic identifiers must be unique.")
        excluded = set(self.excluded_topic_ids)
        selected = set(self.plan.selected_topic_ids)
        if len(excluded) != len(self.excluded_topic_ids):
            raise ValueError("Excluded identifiers must be unique.")
        if not excluded.issubset(topics) or not selected.issubset(topics):
            raise ValueError("Every selection and exclusion must reference a library topic.")
        if excluded & selected:
            raise ValueError("An excluded topic cannot be selected in the active plan.")
        # Evidence concerns are advisory topic reviews, not structural errors.
        # Keep uncertain references saveable/selectable; review_candidate checks
        # them against the current documents whenever an unselected card is shown.
        if any(not item.strip() or len(item) > 3000 for item in self.feedback):
            raise ValueError("Feedback must be nonempty and bounded.")
        if self.modified_at < self.created_at:
            raise ValueError("Workspace modification time cannot precede its creation time.")
        return self
