"""Verify structural contracts, safe portable snapshots, and authoritative reports."""

import csv
import hashlib
import json
from datetime import date, datetime, timezone
from io import StringIO

import pytest
from pydantic import ValidationError

from exports.csv_exporter import CSV_COLUMNS, export_csv
from exports.markdown_exporter import export_markdown
from models.generation_result import GenerationResult
from models.plan import Plan
from models.topic import EvidenceReference, TopicCandidate, TopicIdea
from models.workspace import DocumentRecord, Workspace
from storage.workspace_store import load_workspace, save_workspace


def example_workspace(count: int = 3, finalized: bool = True) -> Workspace:
    """Small fictional evidence, with one available-but-unselected topic at the end."""
    observations = [f"Classroom {number} has a labelled sorting bin." for number in range(count)]
    locations = {f"Row {number + 1}": text for number, text in enumerate(observations)}
    document = DocumentRecord(
        document_id=hashlib.sha256(b"fictional school report").hexdigest(),
        filename="school.csv", file_type="csv", size_bytes=23,
        content="\n\n".join(f"[{label}]\n{text}" for label, text in locations.items()),
        locations=locations, warnings=["Fictional school fixture; no real observations."],
        participated=True,
    )
    topics = [TopicIdea(
        title=f"Sorting labels in classroom {number}", core_insight=text,
        context=f"The fictional school report documents the labelled bin in classroom {number}.",
        target_audience="School students", suggested_format="Noticeboard explainer",
        sources=[EvidenceReference(document_id=document.document_id, filename=document.filename,
                                   location=f"Row {number + 1}", excerpt=text)],
    ) for number, text in enumerate(observations)]
    selected = [topic.topic_id for topic in topics[:-1]][::-1]
    plan = Plan(
        name="School sorting plan", mode="Campaign", audience="Students",
        goal="Explain the documented bin labels", guidance="Use accessible language",
        selected_topic_ids=selected,
        status="FINALIZED" if finalized else "READY_FOR_REVIEW",
        finalized_at=datetime.now(timezone.utc) if finalized else None,
    )
    return Workspace(name="Greenfield School", documents=[document], topics=topics, plan=plan,
                     excluded_topic_ids=[topics[-1].topic_id], pool_revision=1, request_round=2,
                     last_successful_request="fictional-request", sufficiency_note="Supported fictional topics.")


def test_round_trip_preserves_all_working_material_and_stable_ids() -> None:
    workspace = example_workspace()
    reopened = load_workspace(save_workspace(workspace))
    assert reopened == workspace
    assert reopened.documents[0].content_characters == len(reopened.documents[0].content)
    assert reopened.plan.selected_topic_ids == workspace.plan.selected_topic_ids
    assert reopened.excluded_topic_ids == workspace.excluded_topic_ids
    assert reopened.topics[0].sources == workspace.topics[0].sources


def test_topic_context_is_required_and_batch_limit_is_not_library_limit() -> None:
    workspace = example_workspace(count=14)
    assert len(workspace.plan.selected_topic_ids) == 13
    assert load_workspace(save_workspace(workspace)) == workspace
    candidate = workspace.topics[0].model_dump(exclude={"topic_id", "origin"})
    with pytest.raises(ValidationError):
        GenerationResult(candidates=[candidate] * 11, sufficiency_note="Too many candidates.")
    candidate.pop("context")
    with pytest.raises(ValidationError):
        TopicCandidate.model_validate(candidate)
    assert GenerationResult(candidates=[], sufficiency_note="No additional distinct evidence.").candidates == []


@pytest.mark.parametrize("mutator", [
    lambda value: value.update(schema_version=2),
    lambda value: value.update(schema_version=True),
    lambda value: value.update(api_key="do-not-accept"),
    lambda value: value["workspace"].update(api_key="do-not-accept"),
    lambda value: value["workspace"].pop("name"),
    lambda value: value["workspace"]["plan"].pop("mode"),
    lambda value: value["workspace"]["documents"][0].update(size_bytes=True),
    lambda value: value["workspace"]["documents"][0].update(filename="C:\\private\\school.csv"),
    lambda value: value["workspace"]["documents"][0].update(content="Different from locations"),
    lambda value: value["workspace"]["topics"][-1]["sources"][0].update(document_id="a" * 64),
    lambda value: value["workspace"]["topics"][-1]["sources"][0].update(filename="wrong.csv"),
    lambda value: value["workspace"]["topics"][-1]["sources"][0].update(location="Invented page"),
    lambda value: value["workspace"]["topics"][-1]["sources"][0].update(excerpt="Invented supporting text"),
    lambda value: value["workspace"]["plan"]["selected_topic_ids"].append("b" * 32),
    lambda value: value["workspace"]["excluded_topic_ids"].append(value["workspace"]["plan"]["selected_topic_ids"][0]),
    lambda value: value["workspace"]["plan"].update(finalized_at=None),
])
def test_invalid_load_is_transactional_including_late_evidence_failure(mutator) -> None:
    active = example_workspace()
    before = active.model_dump(mode="json")
    payload = json.loads(save_workspace(active))
    mutator(payload)
    with pytest.raises(ValueError):
        candidate = load_workspace(json.dumps(payload).encode())
        active = candidate
    assert active.model_dump(mode="json") == before


def test_no_environment_secrets_raw_uploads_or_arbitrary_objects_are_saved(monkeypatch, tmp_path) -> None:
    secret = "fixture-private-api-key"
    monkeypatch.setenv("GEMINI_API_KEY", secret)
    workspace = example_workspace()
    object.__setattr__(workspace, "api_key", secret)
    object.__setattr__(workspace, "raw_upload", b"original binary must not survive")
    saved = save_workspace(workspace)
    assert secret.encode() not in saved
    assert b"raw_upload" not in saved
    assert b"original binary" not in saved
    marker = tmp_path / "executed.txt"
    attack = f"__import__('pathlib').Path({str(marker)!r}).write_text('executed')"
    with pytest.raises(ValueError):
        load_workspace(attack.encode())
    assert not marker.exists()


@pytest.mark.parametrize("data", [b"", b"not-json", b"[]", b"null", b"\xff", b'{"x":1,"x":2}', b'{"x":NaN}'])
def test_malformed_workspace_files_are_rejected(data: bytes) -> None:
    with pytest.raises(ValueError):
        load_workspace(data)


def test_snapshot_limits_and_busy_handling(monkeypatch) -> None:
    workspace = example_workspace()
    workspace.busy = True
    with pytest.raises(ValueError, match="processing"):
        save_workspace(workspace)
    workspace.busy = False
    payload = json.loads(save_workspace(workspace))
    payload["workspace"]["busy"] = True
    assert not load_workspace(json.dumps(payload).encode()).busy
    monkeypatch.setattr("storage.workspace_store.MAX_WORKSPACE_BYTES", 1024)
    with pytest.raises(ValueError, match="limit"):
        load_workspace(b"x" * 1025)
    with pytest.raises(ValueError, match="limit"):
        save_workspace(workspace)


def test_snapshot_collection_guard_is_separate_from_campaign_size(monkeypatch) -> None:
    workspace = example_workspace(count=14)
    assert len(workspace.plan.selected_topic_ids) > 10
    data = save_workspace(workspace)
    monkeypatch.setattr("storage.workspace_store.MAX_SAVED_TOPICS", 13)
    with pytest.raises(ValueError, match="resource limit"):
        save_workspace(workspace)
    with pytest.raises(ValueError, match="resource limit"):
        load_workspace(data)


def test_import_errors_do_not_echo_private_field_values() -> None:
    payload = json.loads(save_workspace(example_workspace()))
    payload["workspace"]["topics"][-1]["sources"][0]["excerpt"] = "SECRET PRIVATE PATIENT TEXT"
    with pytest.raises(ValueError) as error:
        load_workspace(json.dumps(payload).encode())
    assert "SECRET PRIVATE" not in str(error.value)


def test_week_slots_dates_and_explicit_shortfall_acknowledgement() -> None:
    workspace = example_workspace()
    selected = workspace.plan.selected_topic_ids
    workspace.plan = Plan(
        name="A short school week", mode="Week", weekly_days=5,
        selected_topic_ids=selected, day_assignments={0: selected[0], 2: selected[1]},
        start_date=date(2026, 10, 19), status="FINALIZED", shortfall_acknowledged=True,
        finalized_at=datetime.now(timezone.utc),
    )
    reopened = load_workspace(save_workspace(workspace))
    assert reopened.plan.day_assignments == {0: selected[0], 2: selected[1]}
    markdown = export_markdown(reopened)
    assert "Monday — 2026-10-19" in markdown
    assert "Wednesday — 2026-10-21" in markdown
    assert markdown.count("Unfilled slot") == 3
    assert "Shorter plan approved" in markdown
    rows = list(csv.DictReader(StringIO(export_csv(reopened).decode("utf-8-sig"))))
    assert [row["weekday"] for row in rows] == ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    assert [row["date"] for row in rows] == [f"2026-10-{day}" for day in range(19, 24)]
    assert rows[1]["slot_status"] == "Unfilled" and rows[1]["topic_title"] == ""
    assert rows[2]["topic_title"] == workspace.topics[0].title


@pytest.mark.parametrize("changes", [
    {"start_date": date(2026, 10, 20)},
    {"target": 5},
    {"day_assignments": {7: "1" * 32}},
    {"mode": "Campaign", "start_date": date(2026, 10, 19)},
    {"weekly_days": 6},
    {"mode": "Campaign", "target": True},
    {"start_date": 0},
    {"start_date": date(9999, 12, 27), "weekly_days": 7},
    {"status": "FINALIZED", "finalized_at": datetime.now(timezone.utc)},
])
def test_inconsistent_plans_are_rejected(changes) -> None:
    with pytest.raises(ValidationError):
        Plan(**changes)


def test_week_calendar_overflow_load_is_transactional() -> None:
    active = example_workspace()
    before = active.model_dump(mode="json")
    selected = active.plan.selected_topic_ids
    payload = json.loads(save_workspace(active))
    payload["workspace"]["plan"].update(
        mode="Week", weekly_days=7, start_date="9999-12-27",
        day_assignments={str(index): topic_id for index, topic_id in enumerate(selected)},
        shortfall_acknowledged=True,
    )
    with pytest.raises(ValueError, match="validation failed"):
        candidate = load_workspace(json.dumps(payload).encode())
        active = candidate
    assert active.model_dump(mode="json") == before


def test_campaign_exports_only_finalized_selected_order_and_supporting_context() -> None:
    workspace = example_workspace()
    first, second = [next(topic for topic in workspace.topics if topic.topic_id == key)
                     for key in workspace.plan.selected_topic_ids]
    markdown = export_markdown(workspace)
    assert markdown.index(first.title) < markdown.index(second.title)
    assert workspace.topics[-1].title not in markdown
    assert first.context in markdown
    assert "school.csv" in markdown and "Row 2" in markdown
    assert "Fictional school fixture" in markdown
    assert "## Planning brief" in markdown
    csv_bytes = export_csv(workspace)
    assert csv_bytes.startswith(b"\xef\xbb\xbf")
    reader = csv.DictReader(StringIO(csv_bytes.decode("utf-8-sig")))
    assert reader.fieldnames == CSV_COLUMNS
    rows = list(reader)
    assert [row["topic_title"] for row in rows] == [first.title, second.title]
    assert rows[0]["topic_context"] == first.context
    assert rows[0]["date"] == rows[0]["weekday"] == ""


def test_csv_quoting_unicode_multiline_and_formula_neutralization() -> None:
    workspace = example_workspace()
    workspace.name = '=HYPERLINK("https://invalid")'
    topic = workspace.topics[1]
    topic.title = '@School, "sorting" — विद्यार्थी'
    topic.context = "A useful first context line.\nA second context line, with a comma."
    topic.target_audience = "  +students"
    rows = list(csv.DictReader(StringIO(export_csv(workspace).decode("utf-8-sig"))))
    assert rows[0]["workspace_name"].startswith("'=")
    assert rows[0]["topic_title"] == "'" + topic.title
    assert rows[0]["topic_context"] == topic.context
    assert rows[0]["target_audience"] == "'+students"


@pytest.mark.parametrize("exporter", [export_markdown, export_csv])
def test_export_requires_nonempty_finalized_and_rejects_stale_invalid_state(exporter) -> None:
    workspace = example_workspace(finalized=False)
    with pytest.raises(ValueError, match="Finalize"):
        exporter(workspace)
    with pytest.raises(ValueError):
        exporter(Workspace())
    workspace = example_workspace()
    workspace.plan.selected_topic_ids.clear()
    with pytest.raises(ValueError, match="inconsistent"):
        exporter(workspace)


def test_source_and_identifier_collection_integrity() -> None:
    workspace = example_workspace()
    value = workspace.model_dump()
    value["documents"].append(value["documents"][0].copy())
    with pytest.raises(ValidationError, match="unique"):
        Workspace.model_validate(value)
    value = workspace.model_dump()
    value["topics"].append(value["topics"][0].copy())
    with pytest.raises(ValidationError, match="unique"):
        Workspace.model_validate(value)
    source = workspace.documents[0].model_dump()
    source["size_bytes"] = 0
    with pytest.raises(ValidationError):
        DocumentRecord.model_validate(source)
