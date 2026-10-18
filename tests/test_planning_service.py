"""Complete local workflows use real parsers and deterministic simulated providers."""

import csv
from datetime import date
from io import StringIO
import json

import pytest

from ai.gemini_client import GenerationError
from ai.response_validator import review_candidate
from exports.csv_exporter import export_csv
from exports.markdown_exporter import export_markdown
from models.generation_result import GenerationResult
from models.topic import EvidenceReference, TopicCandidate
from models.workspace import Workspace
from storage.workspace_store import load_workspace, save_workspace
from tests.conftest import make_candidate
from workflow.plan_manager import (
    assign_day, configure_plan, deselect_topic, exclude_topic, finalize_plan, move_topic,
    reopen_plan, restore_topic, select_topic,
)
from workflow.planning_service import generate_batch, ingest_files
from workflow.state_manager import new_plan


class SimulatedProvider:
    """Return predeclared data while recording only intentional generation calls."""

    def __init__(self, candidates=None, error=None, on_call=None):
        self.candidates = list(candidates or [])
        self.error = error
        self.calls = []
        self.on_call = on_call

    def generate(self, prompt, capacity):
        self.calls.append((prompt, capacity))
        if self.on_call:
            self.on_call()
        if self.error:
            raise self.error
        return GenerationResult(candidates=self.candidates,
            sufficiency_note="Only these distinct fictional recorded observations are supported.")


def real_csv_workspace() -> Workspace:
    """Parse genuine CSV bytes, retaining row identities rather than invented evidence."""
    state = Workspace(name="Fictional ward records")
    records = "Ward,Sorted waste kg\n1,10\n2,20\n3,30\n4,40\n5,50\n"
    feedback = ingest_files(state, [("fictional_wards.csv", records.encode("utf-8"))])
    assert feedback == ["Added fictional_wards.csv."]
    assert len(state.documents) == 1
    return state


def parsed_candidate(state: Workspace, number: int) -> TopicCandidate:
    document = state.documents[0]
    location = f"CSV, row {number + 1}"
    excerpt = document.locations[location]
    return TopicCandidate(
        title=f"Sorted waste observation in Ward {number}",
        core_insight=f"Ward {number} records {number * 10} kg of sorted waste.",
        context=f"The CSV records this ward-specific sorted waste observation: {excerpt}",
        target_audience="Residents", suggested_format="Infographic",
        sources=[EvidenceReference(document_id=document.document_id, filename=document.filename,
            location=location, excerpt=excerpt)],
    )


def test_real_csv_to_week_review_finalization_exports_and_workspace_reopen():
    state = real_csv_workspace()
    configure_plan(state, name="Fictional school week", mode="Week", weekly_days=5,
        start_date=date(2026, 10, 19), audience="Residents", goal="Explain the ward records")
    provider = SimulatedProvider([parsed_candidate(state, index) for index in (1, 2, 3)])
    feedback = generate_batch(state, provider=provider)
    assert len(provider.calls) == 1
    assert len(state.topics) == 3
    assert state.plan.status == "DRAFT"
    assert state.plan.remaining_slots == 5
    assert not state.plan.selected_topic_ids
    assert state.documents[0].participated
    assert any("not padded" in item for item in feedback)

    first, second, third = [item.topic_id for item in state.topics]
    select_topic(state, first)
    select_topic(state, third)
    exclude_topic(state, second)
    restore_topic(state, second)
    assert second not in state.plan.selected_topic_ids
    select_topic(state, second)
    assign_day(state, first, 4)
    move_topic(state, third, -1)
    assert len(provider.calls) == 1  # Review and assignment do not spend API quota.
    with pytest.raises(ValueError, match="Finalize"):
        export_markdown(state)
    finalize_plan(state, acknowledge_shortfall=True)
    markdown = export_markdown(state)
    table = list(csv.DictReader(StringIO(export_csv(state).decode("utf-8-sig"))))
    assert len(table) == 5
    assert [row["weekday"] for row in table] == ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    assert [row["date"] for row in table] == [f"2026-10-{day}" for day in range(19, 24)]
    assert sum(row["slot_status"] == "Unfilled" for row in table) == 2
    selected_titles = [row["topic_title"] for row in table if row["topic_title"]]
    lookup = {topic.topic_id: topic for topic in state.topics}
    assert selected_titles == [lookup[identity].title for identity in state.plan.selected_topic_ids]
    assert r"fictional\_wards.csv" in markdown
    assert "CSV, row" in markdown
    assert "Unfilled slot" in markdown
    assert "Shorter plan approved" in markdown

    saved = save_workspace(state)
    reopened = load_workspace(saved)
    assert reopened.model_dump(mode="json") == state.model_dump(mode="json")
    assert export_markdown(reopened) == markdown
    assert export_csv(reopened) == export_csv(state)
    assert len(provider.calls) == 1
    reopen_plan(reopened)
    deselect_topic(reopened, first)
    with pytest.raises(ValueError, match="Finalize"):
        export_csv(reopened)


def test_campaign_can_accumulate_more_than_ten_with_unchanged_sources(workspace):
    configure_plan(workspace, name="Open campaign", mode="Campaign")
    initial_revision = workspace.pool_revision
    first = SimulatedProvider([make_candidate(workspace, index) for index in range(1, 11)])
    generate_batch(workspace, provider=first)
    first_success = workspace.last_successful_request
    assert len(workspace.topics) == 10
    assert workspace.plan.status == "DRAFT"
    assert workspace.plan.finalized_at is None
    second = SimulatedProvider([make_candidate(workspace, index) for index in range(11, 16)])
    generate_batch(workspace, provider=second)
    assert len(workspace.topics) == 15
    assert not workspace.plan.selected_topic_ids
    for topic in workspace.topics:
        select_topic(workspace, topic.topic_id)
    assert workspace.pool_revision == initial_revision
    assert workspace.request_round == 2
    assert workspace.last_successful_request != first_success
    assert workspace.plan.effective_target is None
    assert workspace.plan.remaining_slots is None
    assert first.calls[0][1] == second.calls[0][1] == 10
    for topic in workspace.topics[:10]:
        assert topic.title in second.calls[0][0]
    finalize_plan(workspace)
    assert len(list(csv.DictReader(StringIO(export_csv(workspace).decode("utf-8-sig")))) ) == 15


def test_fixed_target_bounds_next_batch_and_never_auto_finalizes(workspace):
    configure_plan(workspace, name="Twelve supported observations", mode="Campaign", target=12)
    first = SimulatedProvider([make_candidate(workspace, index) for index in range(1, 11)])
    generate_batch(workspace, provider=first)
    assert workspace.plan.remaining_slots == 12
    for topic in workspace.topics:
        select_topic(workspace, topic.topic_id)
    assert workspace.plan.remaining_slots == 2
    second = SimulatedProvider([make_candidate(workspace, index) for index in range(11, 14)])
    generate_batch(workspace, provider=second)
    assert second.calls[0][1] == 2
    assert len(workspace.topics) == 13  # Extra returned topics stay in the library.
    assert workspace.plan.remaining_slots == 2
    for topic in workspace.topics[10:12]:
        select_topic(workspace, topic.topic_id)
    assert workspace.plan.status == "READY_FOR_REVIEW"
    before = workspace.model_dump(mode="json")
    with pytest.raises(ValueError, match="target is full"):
        generate_batch(workspace, provider=second)
    assert len(second.calls) == 1
    assert workspace.model_dump(mode="json") == before


def test_zero_new_success_consumes_one_explicit_round_and_preserves_topics(workspace):
    configure_plan(workspace, name="Open", mode="Campaign")
    generate_batch(workspace, provider=SimulatedProvider([make_candidate(workspace, 1)]))
    before_topics = [topic.model_dump() for topic in workspace.topics]
    selected = list(workspace.plan.selected_topic_ids)
    provider = SimulatedProvider([])
    feedback = generate_batch(workspace, provider=provider)
    assert workspace.request_round == 2
    assert [topic.model_dump() for topic in workspace.topics] == before_topics
    assert workspace.plan.selected_topic_ids == selected
    assert not workspace.busy
    assert any("No new topics" in message for message in feedback)
    # An additional user action, using exactly the same documents, is a new round.
    generate_batch(workspace, provider=provider)
    assert workspace.request_round == 3
    assert len(provider.calls) == 2


def test_flagged_candidate_round_is_saveable_selectable_and_exportable(workspace):
    configure_plan(workspace, name="Open", mode="Campaign", audience="Residents", goal="Recorded data")
    generate_batch(workspace, provider=SimulatedProvider([make_candidate(workspace, 1)]))
    invalid = make_candidate(workspace, 2)
    invalid.sources[0].location = "Invented row"
    provider = SimulatedProvider([invalid])
    generate_batch(workspace, provider=provider)
    assert len(workspace.topics) == 2
    assert workspace.request_round == 2
    assert not workspace.plan.selected_topic_ids
    assert len(provider.calls) == 1
    reopened = load_workspace(save_workspace(workspace))
    topic = reopened.topics[-1]
    assert review_candidate(topic, reopened.documents)
    select_topic(reopened, topic.topic_id)
    finalize_plan(reopened)
    assert load_workspace(save_workspace(reopened)) == reopened
    markdown = export_markdown(reopened)
    table = export_csv(reopened).decode('utf-8-sig')
    for exported in (markdown, table):
        assert topic.title in exported
        assert 'unverified' not in exported.lower()
        assert 'needs review' not in exported.lower()


@pytest.mark.parametrize("category", ["timeout", "provider", "invalid_output", "quota"])
def test_later_failure_preserves_library_selection_exclusions_and_brief(workspace, category):
    configure_plan(workspace, name="Keep my plan", mode="Campaign", audience="Residents",
        goal="Explain sorted waste records", guidance="Use only documented ward observations.")
    generate_batch(workspace, provider=SimulatedProvider([make_candidate(workspace, i) for i in (1, 2, 3)]))
    for topic in workspace.topics:
        select_topic(workspace, topic.topic_id)
    exclude_topic(workspace, workspace.topics[0].topic_id)
    move_topic(workspace, workspace.topics[-1].topic_id, -1)
    before = workspace.model_dump(mode="json")
    provider = SimulatedProvider(error=GenerationError(category, "A safe recoverable test failure", True))
    with pytest.raises(GenerationError):
        generate_batch(workspace, provider=provider)
    assert workspace.model_dump(mode="json") == before
    assert not workspace.busy


def test_all_readable_candidates_remain_available_with_local_review_notes(workspace):
    configure_plan(workspace, name="Open", mode="Campaign")
    first = make_candidate(workspace, 1)
    generate_batch(workspace, provider=SimulatedProvider([first]))
    excluded_id = workspace.topics[0].topic_id
    exclude_topic(workspace, excluded_id)
    unsupported = make_candidate(workspace, 3)
    unsupported.core_insight = "Ward 3 reports 99999 kg of sorted waste."
    provider = SimulatedProvider([first, make_candidate(workspace, 2), unsupported])
    feedback = generate_batch(workspace, provider=provider)
    assert len(workspace.topics) == 4
    assert workspace.excluded_topic_ids == [excluded_id]
    assert not workspace.plan.selected_topic_ids
    assert any("excluded" in item for item in feedback)
    assert any("numeric" in item for item in feedback)
    assert '"state": "excluded"' in provider.calls[0][0]


def test_reserved_generation_blocks_another_operation_and_releases_busy(workspace):
    def check_reserved():
        assert workspace.busy
        with pytest.raises(ValueError, match="current operation"):
            new_plan(workspace)
        with pytest.raises(ValueError, match="current operation"):
            generate_batch(workspace, provider=SimulatedProvider([]))

    provider = SimulatedProvider([make_candidate(workspace, 1)], on_call=check_reserved)
    generate_batch(workspace, provider=provider)
    assert not workspace.busy


def test_new_plan_retains_sources_angles_exclusions_without_provider_calls(workspace):
    configure_plan(workspace, name="Open", mode="Campaign")
    provider = SimulatedProvider([make_candidate(workspace, index) for index in (1, 2)])
    generate_batch(workspace, provider=provider)
    exclude_topic(workspace, workspace.topics[0].topic_id)
    before_sources = [document.model_dump() for document in workspace.documents]
    before_topics = [topic.model_dump() for topic in workspace.topics]
    exclusions = list(workspace.excluded_topic_ids)
    new_plan(workspace, "Next week's plan")
    assert workspace.plan.mode == "Week"
    assert not workspace.plan.selected_topic_ids
    assert [document.model_dump() for document in workspace.documents] == before_sources
    assert [topic.model_dump() for topic in workspace.topics] == before_topics
    assert workspace.excluded_topic_ids == exclusions
    assert len(provider.calls) == 1


def test_saved_uncertain_reference_reopens_for_review_without_replacing_active_work(workspace):
    configure_plan(workspace, name="Open", mode="Campaign")
    generate_batch(workspace, provider=SimulatedProvider([make_candidate(workspace, 1)]))
    before = workspace.model_dump(mode="json")
    payload = json.loads(save_workspace(workspace))
    payload["workspace"]["topics"][0]["sources"][0]["location"] = "Missing after full structural validation"
    reopened = load_workspace(json.dumps(payload).encode("utf-8"))
    assert review_candidate(reopened.topics[0], reopened.documents)
    assert workspace.model_dump(mode="json") == before


def test_ingestion_handles_each_file_independently_and_never_calls_provider():
    workspace = Workspace()
    feedback = ingest_files(workspace, [
        ("empty.csv", b""), ("valid.csv", b"Ward,Sorted waste kg\n1,10\n"),
        ("unsupported.exe", b"not a source"),
    ])
    assert len(feedback) == 3
    assert [document.filename for document in workspace.documents] == ["valid.csv"]
    assert workspace.request_round == 0
    assert not workspace.topics
