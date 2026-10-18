"""Tolerant local review keeps real text traceable without changing its meaning."""

import pytest

from ai.response_validator import review_candidate, validate_candidates, validate_evidence
from documents.evidence import source_passage
from documents.extraction import canonical_content
from models.generation_result import GenerationResult
from storage.workspace_store import load_workspace, save_workspace
from tests.conftest import make_candidate


@pytest.mark.parametrize('excerpt,original', [
    ('organic waste at source', 'organic\nwaste  at\u00a0source'),
    ('The "office" sorting labels', 'The “ofﬁce” sorting labels'),
    ('biodegradable waste', 'bio\u00addegradable waste'),
    ('separation of organic waste', 'separa-\r\n  tion of organic waste'),
])
def test_formatting_match_recovers_the_original_passage(excerpt, original):
    assert source_passage(excerpt, 'Introduction. ' + original + '. Findings.') == original


@pytest.mark.parametrize('excerpt,original', [
    ('12% of waste', '12 kg of waste'),
    ('20 kg of waste', '10 kg of waste'),
    ('sorting is effective', 'sorting is not effective'),
    ('12 kg of waste', '1\n2 kg of waste'),
    ('-12 kg of waste', '-1\n2 kg of waste'),
    ('', 'No usable quote supplied.'),
])
def test_changed_facts_and_missing_words_are_not_treated_as_formatting(excerpt, original):
    assert source_passage(excerpt, original) is None


def test_normalized_quote_is_restored_without_mutating_provider_output(workspace):
    document = workspace.documents[0]
    original = 'Ward 1 reports\n10 kg of sorted waste.'
    document.locations['Row 1'] = original
    document.content = canonical_content(document.locations)
    proposed = make_candidate(workspace, 1)
    proposed.sources[0].excerpt = 'Ward 1 reports 10 kg of sorted waste.'
    result = GenerationResult(candidates=[proposed], sufficiency_note='A documented observation.')
    batch = validate_candidates(result, workspace.documents, [], [], 5)
    assert not review_candidate(batch.candidates[0], workspace.documents)
    assert batch.candidates[0].sources[0].excerpt == original
    assert proposed.sources[0].excerpt != original


@pytest.mark.parametrize('field,value', [
    ('document_id', 'a' * 64), ('filename', 'missing.csv'),
    ('location', 'Missing page'), ('excerpt', 'An unlocated but readable passage.'),
])
def test_uncertain_references_roundtrip_and_keep_their_local_review_status(workspace, field, value):
    from models.topic import TopicIdea

    proposed = make_candidate(workspace, 1)
    setattr(proposed.sources[0], field, value)
    workspace.topics = [TopicIdea(**proposed.model_dump())]
    reopened = load_workspace(save_workspace(workspace))
    assert reopened == workspace
    assert validate_evidence(reopened.topics[0], reopened.documents)
    assert review_candidate(reopened.topics[0], reopened.documents)


def test_restoring_equivalent_quotes_does_not_create_duplicate_reference_errors(workspace):
    proposed = make_candidate(workspace, 1)
    reference = proposed.sources[0]
    proposed.sources.append(reference.model_copy(update={
        'excerpt': reference.excerpt.replace('reports ', 'reports\n'),
    }))
    batch = validate_candidates(
        GenerationResult(candidates=[proposed], sufficiency_note='A documented observation.'),
        workspace.documents, [], [], 5,
    )
    assert len(batch.candidates[0].sources) == 1
    assert len(proposed.sources) == 2


def test_readable_topic_without_citations_is_kept_for_manual_selection(workspace):
    from ai.topic_generator import generate_topics
    from models.topic import TopicIdea
    from unittest.mock import Mock
    from workflow.plan_manager import select_topic

    proposed = make_candidate(workspace, 1).model_copy(update={'sources': []})
    provider = Mock()
    provider.feedback = []
    provider.generate.return_value = GenerationResult(
        candidates=[proposed], sufficiency_note='An idea requiring manual evidence review.',
    )
    batch = generate_topics(workspace, 5, provider)
    assert len(batch.candidates) == 1
    assert 'no supporting source references' in review_candidate(
        batch.candidates[0], workspace.documents,
    )[0]
    workspace.topics = [TopicIdea(**batch.candidates[0].model_dump())]
    select_topic(workspace, workspace.topics[0].topic_id)
    assert load_workspace(save_workspace(workspace)) == workspace
    provider.generate.assert_called_once()
