"""Regression checks for identity, source protection, memory and transactional changes."""

import pytest

from models.workspace import Workspace
from tests.conftest import seed_topics
from workflow.plan_manager import exclude_topic
from workflow.state_manager import (
    add_document, create_document, new_plan, remove_document, rename_workspace, reset_workspace,
)


def test_independent_empty_workspaces() -> None:
    """Each browser session must own independent collections."""
    first, second = Workspace(), Workspace()
    add_document(first, create_document('a.csv', b'a', 'Readable fictional source'))
    assert second.documents == []
    assert second.pool_revision == 0


def test_duplicate_bytes_retains_name_and_revision(workspace: Workspace) -> None:
    """Same content under a new name is not a new input revision."""
    source = workspace.documents[0]
    revision = workspace.pool_revision
    duplicate = source.model_copy(update={'filename': 'renamed.csv'})
    assert 'Duplicate' in add_document(workspace, duplicate)
    assert workspace.pool_revision == revision
    assert workspace.documents == [source]


def test_name_conflict_is_atomic(workspace: Workspace) -> None:
    """Different content cannot overwrite an existing citation name."""
    before = workspace.model_dump()
    with pytest.raises(ValueError, match='Rename'):
        add_document(workspace, create_document('FICTIONAL.csv', b'different', 'Different text'))
    assert workspace.model_dump() == before


def test_cited_excluded_source_protected(workspace: Workspace) -> None:
    """An excluded record still retains restorable evidence."""
    seed_topics(workspace)
    exclude_topic(workspace, workspace.topics[0].topic_id)
    with pytest.raises(ValueError, match='retained topic'):
        remove_document(workspace, workspace.documents[0].document_id)


def test_uncited_removal_changes_revision(workspace: Workspace) -> None:
    """Participation alone does not lock an uncited document."""
    workspace.documents[0].participated = True
    remove_document(workspace, workspace.documents[0].document_id)
    assert workspace.pool_revision == 2
    assert workspace.documents == []


def test_new_plan_retains_reusable_material(workspace: Workspace) -> None:
    """New plan and reset are intentionally distinct operations."""
    seed_topics(workspace)
    exclude_topic(workspace, workspace.topics[0].topic_id)
    old_id = workspace.plan.plan_id
    new_plan(workspace, 'Another week')
    assert workspace.plan.plan_id != old_id
    assert len(workspace.documents) == 1 and len(workspace.topics) == 3
    assert workspace.excluded_topic_ids == [workspace.topics[0].topic_id]
    reset_workspace(workspace)
    assert not workspace.documents and not workspace.topics and not workspace.excluded_topic_ids


def test_invalid_rename_and_busy_edit_preserve_state(workspace: Workspace) -> None:
    """Boundary validation is applied before replacing current state."""
    before = workspace.model_dump()
    with pytest.raises(ValueError):
        rename_workspace(workspace, '')
    assert workspace.model_dump() == before
    workspace.busy = True
    with pytest.raises(ValueError, match='Wait'):
        add_document(workspace, create_document('a.csv', b'a', 'Source text'))
    with pytest.raises(ValueError, match='Wait'):
        reset_workspace(workspace)


@pytest.mark.parametrize('filename,data,text', [
    ('x.txt', b'x', 'Text'), ('x.csv', b'', 'Text'),
    ('x.csv', b'x', '  '), ('../x.csv', b'x', 'Text'),
])
def test_invalid_source_records(filename: str, data: bytes, text: str) -> None:
    """Reject unusable metadata and extraction without creating source records."""
    with pytest.raises(ValueError):
        create_document(filename, data, text)
