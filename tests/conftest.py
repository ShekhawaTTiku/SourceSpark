"""Small fictional workspace fixtures shared by rule and integration checks."""

import pytest

from models.topic import EvidenceReference, TopicCandidate, TopicIdea
from models.workspace import Workspace
from workflow.state_manager import add_document, create_document


@pytest.fixture
def workspace() -> Workspace:
    """Create an independent source-backed workspace without a real API key."""
    state = Workspace()
    locations = {f'Row {number}': f'Ward {number} reports {number * 10} kg of sorted waste.'
                 for number in range(1, 31)}
    content = '\n'.join(locations.values())
    document = create_document('fictional.csv', content.encode(), content, locations=locations)
    add_document(state, document)
    return state


def make_candidate(workspace: Workspace, number: int) -> TopicCandidate:
    """Use one unique supported row, avoiding model-dependent outputs."""
    source = workspace.documents[0]
    excerpt = source.locations[f'Row {number}']
    return TopicCandidate(
        title=f'Sorted waste recorded in Ward {number}', core_insight=excerpt,
        context=f'The source records this ward-specific observation: {excerpt}',
        target_audience='Residents', suggested_format='Infographic',
        sources=[EvidenceReference(document_id=source.document_id, filename=source.filename,
                                   location=f'Row {number}', excerpt=excerpt)],
    )


def seed_topics(workspace: Workspace, count: int = 3) -> None:
    """Populate only the reusable library, leaving plan selection to each test."""
    workspace.topics = [TopicIdea(**make_candidate(workspace, number).model_dump())
                        for number in range(1, count + 1)]
