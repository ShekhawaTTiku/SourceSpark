"""Serialize explicit snapshots and validate imports before callers replace state."""

import json
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from config.settings import MAX_SAVED_TOPICS, MAX_WORKSPACE_BYTES
from models.plan import Plan
from models.topic import EvidenceReference, TopicIdea
from models.workspace import DocumentRecord, Workspace


SCHEMA_VERSION = 1


def _complete_fields(value: Any, expected: set[str]) -> None:
    """Saved records are complete: missing fields must not acquire misleading defaults."""
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError("The workspace file has missing or unsupported record fields.")


def _validate_shape(payload: Any) -> dict[str, Any]:
    _complete_fields(payload, {"schema_version", "saved_at", "workspace"})
    if type(payload["schema_version"]) is not int or payload["schema_version"] != SCHEMA_VERSION:
        raise ValueError("Unsupported workspace schema version; this app reads version 1.")
    if not isinstance(payload["saved_at"], str):
        raise ValueError("The workspace file has an invalid save timestamp.")
    try:
        datetime.fromisoformat(payload["saved_at"])
    except ValueError:
        raise ValueError("The workspace file has an invalid save timestamp.") from None
    value = payload["workspace"]
    _complete_fields(value, set(Workspace.model_fields))
    _complete_fields(value["plan"], set(Plan.model_fields))
    for field in ("documents", "topics", "excluded_topic_ids", "feedback"):
        if not isinstance(value[field], list):
            raise ValueError("The workspace file has an invalid collection.")
    if len(value["topics"]) > MAX_SAVED_TOPICS or len(value["excluded_topic_ids"]) > MAX_SAVED_TOPICS:
        raise ValueError("The workspace exceeds the snapshot topic-record resource limit.")
    if not isinstance(value["plan"]["selected_topic_ids"], list):
        raise ValueError("The workspace file has an invalid topic selection.")
    if len(value["plan"]["selected_topic_ids"]) > MAX_SAVED_TOPICS:
        raise ValueError("The workspace exceeds the snapshot selection resource limit.")
    assignments = value["plan"]["day_assignments"]
    if not isinstance(assignments, dict) or any(key not in {str(i) for i in range(7)} for key in assignments):
        raise ValueError("The workspace file has invalid weekly assignments.")
    for document in value["documents"]:
        _complete_fields(document, set(DocumentRecord.model_fields))
    for topic in value["topics"]:
        _complete_fields(topic, set(TopicIdea.model_fields))
        if not isinstance(topic["sources"], list):
            raise ValueError("The workspace file has invalid evidence references.")
        for evidence in topic["sources"]:
            _complete_fields(evidence, set(EvidenceReference.model_fields))
    return value


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("The workspace file contains duplicate JSON fields.")
        result[key] = value
    return result


def _reject_constant(_value: str) -> None:
    raise ValueError("The workspace file contains a nonstandard JSON value.")


def save_workspace(workspace: Workspace) -> bytes:
    """Create a browser-downloadable snapshot without secrets or raw uploaded files."""
    if workspace.busy:
        raise ValueError("Wait until processing finishes before saving the workspace.")
    if len(workspace.topics) > MAX_SAVED_TOPICS:
        raise ValueError("The workspace exceeds the snapshot topic-record resource limit.")
    try:
        # Dumping then rebuilding also checks objects changed through ordinary assignment.
        checked = Workspace.model_validate(workspace.model_dump(mode="python"))
    except (ValidationError, TypeError, ValueError):
        raise ValueError("The current workspace is inconsistent and cannot be saved.") from None
    payload = {
        "schema_version": SCHEMA_VERSION,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "workspace": checked.model_dump(mode="json"),
    }
    data = json.dumps(payload, ensure_ascii=False, allow_nan=False, indent=2).encode("utf-8")
    if len(data) > MAX_WORKSPACE_BYTES:
        raise ValueError("The workspace exceeds the 20 MiB snapshot limit.")
    return data


def load_workspace(data: bytes) -> Workspace:
    """Return a fully validated candidate; this function never changes active state."""
    if not isinstance(data, bytes) or not data:
        raise ValueError("Choose a nonempty workspace JSON file.")
    if len(data) > MAX_WORKSPACE_BYTES:
        raise ValueError("The workspace file exceeds the 20 MiB snapshot limit.")
    try:
        payload = json.loads(
            data.decode("utf-8-sig"), object_pairs_hook=_unique_json_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        raise ValueError("The workspace file is not valid UTF-8 JSON.") from None
    value = _validate_shape(payload)
    try:
        candidate = Workspace.model_validate(value)
    except (ValidationError, TypeError, ValueError, OverflowError):
        # Pydantic errors contain original field values: never expose them to the UI.
        raise ValueError("Workspace validation failed. Check its records, references, and plan state.") from None
    candidate.busy = False
    return candidate
