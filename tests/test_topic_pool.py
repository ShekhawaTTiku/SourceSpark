"""Batch bounds and practical duplicate rules without a total ten-topic limit."""

from models.workspace import Workspace
from tests.conftest import make_candidate, seed_topics
from workflow.topic_pool import accept_topics, is_repeated


def test_batches_accumulate_above_ten(workspace: Workspace) -> None:
    """A per-request ceiling must not cap the workspace library."""
    seed_topics(workspace, 10)
    accepted, feedback = accept_topics(workspace.topics,
                                      [make_candidate(workspace, i) for i in range(11, 21)], 10)
    assert len(workspace.topics) + len(accepted) == 20
    assert feedback == []


def test_normalized_title_and_repeated_insight(workspace: Workspace) -> None:
    """Catch wording/case variants across a batch and the existing library."""
    first = make_candidate(workspace, 1)
    variant = first.model_copy(update={'title': first.title.upper() + '!!!'})
    accepted, feedback = accept_topics([], [first, variant])
    assert len(accepted) == 1 and len(feedback) == 1
    changed_title = first.model_copy(update={'title': 'A completely new headline'})
    assert is_repeated(first, changed_title)


def test_numeric_distinct_observations_not_false_duplicates(workspace: Workspace) -> None:
    """Templated titles can describe different source-supported measurements."""
    assert not is_repeated(make_candidate(workspace, 1), make_candidate(workspace, 2))


def test_capacity_bounds_new_acceptance_not_library(workspace: Workspace) -> None:
    """Respect fixed-target vacancies even if candidates overrun capacity."""
    accepted, feedback = accept_topics([], [make_candidate(workspace, i) for i in range(1, 6)], 2)
    assert len(accepted) == 2 and len(feedback) == 3
    assert accept_topics([], [])[0] == []
