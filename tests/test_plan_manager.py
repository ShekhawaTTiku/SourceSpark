"""Weekly/campaign planning, explicit approval and reversible review actions."""

from datetime import date

import pytest

from models.workspace import Workspace
from tests.conftest import seed_topics
from workflow.plan_manager import (
    assign_day, batch_capacity, configure_plan, deselect_topic, exclude_topic,
    finalize_plan, move_topic, reopen_plan, restore_topic, select_topic,
)


def test_week_target_readiness_is_not_finalization(workspace: Workspace) -> None:
    """Five filled slots require a separate finish action."""
    seed_topics(workspace, 7)
    for topic in workspace.topics[:5]:
        select_topic(workspace, topic.topic_id)
    assert workspace.plan.status == 'READY_FOR_REVIEW'
    assert workspace.plan.finalized_at is None
    assert batch_capacity(workspace) == 0
    finalize_plan(workspace)
    assert workspace.plan.status == 'FINALIZED'
    with pytest.raises(ValueError, match='Reopen'):
        deselect_topic(workspace, workspace.topics[0].topic_id)
    reopen_plan(workspace)
    assert workspace.plan.finalized_at is None


def test_campaign_above_ten_and_optional_target(workspace: Workspace) -> None:
    """User targets and open plans use the same selection layer."""
    seed_topics(workspace, 20)
    configure_plan(workspace, name='Large campaign', mode='Campaign', target=20)
    for topic in workspace.topics:
        select_topic(workspace, topic.topic_id)
    assert len(workspace.plan.selected_topic_ids) == 20
    assert workspace.plan.status == 'READY_FOR_REVIEW'
    configure_plan(workspace, name='Open campaign', mode='Campaign')
    assert workspace.plan.remaining_slots is None
    assert batch_capacity(workspace) == 10


def test_smaller_mode_requires_deliberate_selection(workspace: Workspace) -> None:
    """A mode change cannot silently truncate a seven-topic selection."""
    seed_topics(workspace, 7)
    configure_plan(workspace, name='Full week', mode='Week', weekly_days=7)
    for topic in workspace.topics:
        select_topic(workspace, topic.topic_id)
    before = workspace.model_dump()
    with pytest.raises(ValueError, match='Deselect'):
        configure_plan(workspace, name='Weekdays', mode='Week', weekly_days=5)
    assert workspace.model_dump() == before
    for topic in workspace.topics[-2:]:
        deselect_topic(workspace, topic.topic_id)
    configure_plan(workspace, name='Weekdays', mode='Week', weekly_days=5)
    assert len(workspace.topics) == 7
    assert len(workspace.plan.selected_topic_ids) == 5


def test_selection_exclusion_restore_are_distinct(workspace: Workspace) -> None:
    """Exclude deselects and suppresses; restore does not automatically select."""
    seed_topics(workspace)
    identity = workspace.topics[0].topic_id
    select_topic(workspace, identity)
    deselect_topic(workspace, identity)
    assert identity not in workspace.excluded_topic_ids
    select_topic(workspace, identity)
    exclude_topic(workspace, identity)
    assert identity not in workspace.plan.selected_topic_ids
    with pytest.raises(ValueError, match='Restore'):
        select_topic(workspace, identity)
    restore_topic(workspace, identity)
    assert identity not in workspace.plan.selected_topic_ids
    select_topic(workspace, identity)


def test_week_assignments_swap_and_keep_gaps(workspace: Workspace) -> None:
    """Dates/day changes and order operate without generation."""
    seed_topics(workspace)
    for topic in workspace.topics:
        select_topic(workspace, topic.topic_id)
    first, second, third = [topic.topic_id for topic in workspace.topics]
    assign_day(workspace, first, 1)
    assert workspace.plan.selected_topic_ids == [second, first, third]
    assign_day(workspace, third, 4)
    assert 2 not in workspace.plan.day_assignments
    move_topic(workspace, third, -1)
    assert workspace.plan.selected_topic_ids == [second, third, first]
    assert workspace.request_round == 0
    configure_plan(workspace, name='Dated', mode='Week', start_date=date(2026, 12, 28))
    configure_plan(workspace, name='Tuesday start', mode='Week', start_date=date(2026, 12, 29))
    assert workspace.plan.start_date == date(2026, 12, 29)
    before = workspace.model_dump()
    with pytest.raises(ValueError, match='calendar'):
        configure_plan(workspace, name='Invalid', mode='Week', start_date=date(9999, 12, 31))
    assert workspace.model_dump() == before


def test_empty_and_short_finalization(workspace: Workspace) -> None:
    """Targets do not require filler and empty reports are prohibited."""
    with pytest.raises(ValueError, match='empty'):
        finalize_plan(workspace)
    seed_topics(workspace, 1)
    select_topic(workspace, workspace.topics[0].topic_id)
    with pytest.raises(ValueError, match='Acknowledge'):
        finalize_plan(workspace)
    finalize_plan(workspace, acknowledge_shortfall=True)
    assert workspace.plan.shortfall_acknowledged


def test_brief_change_keeps_libraries(workspace: Workspace) -> None:
    """The brief steers relevance without replacing evidence or retained topics."""
    seed_topics(workspace)
    configure_plan(workspace, name='Students', mode='Week', audience='Students',
                   goal='Explain documented sorting observations', guidance='Use plain language')
    assert len(workspace.topics) == 3 and len(workspace.documents) == 1
