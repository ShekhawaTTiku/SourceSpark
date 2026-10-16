"""Provider failover is bounded, explicit, source-validated and credential-safe."""

from io import BytesIO
import json
from unittest.mock import Mock
from urllib.error import HTTPError, URLError

import pytest

from ai.gemini_client import GeminiClient, GenerationError
from ai.groq_client import GroqClient, _NoRedirect, wire_schema
from ai.provider_chain import ProviderAttempt, ProviderChain, configured_chain
from ai.topic_generator import generate_topics
from config import settings
from models.generation_result import GenerationResult
from models.workspace import Workspace
from storage.workspace_store import save_workspace
from tests.conftest import make_candidate
from workflow.plan_manager import configure_plan
from workflow.planning_service import generate_batch


def answer(workspace: Workspace) -> GenerationResult:
    """Produce a valid source-backed result without consuming API quota."""
    return GenerationResult(candidates=[make_candidate(workspace, 1)],
                            sufficiency_note='Only this recorded fictional observation is supported.')


def attempt(label: str, family: str, *, result=None, error=None) -> tuple[ProviderAttempt, Mock]:
    """Create one observable provider and a lazy route to it."""
    provider = Mock()
    provider.generate.side_effect = error
    provider.generate.return_value = result
    return ProviderAttempt(label, family, lambda: provider), provider


@pytest.mark.parametrize('category', [
    'provider', 'timeout', 'quota', 'authentication', 'configuration',
    'model', 'context', 'request', 'invalid_output',
])
def test_primary_operational_failure_uses_groq(workspace: Workspace, category: str) -> None:
    primary, first = attempt('Gemini primary', 'Gemini', error=GenerationError(category, 'Safe failure'))
    fallback, second = attempt('Groq fallback', 'Groq', result=answer(workspace))
    reserve, third = attempt('Gemini reserve', 'Gemini', result=answer(workspace))
    chain = ProviderChain([primary, fallback, reserve])
    generate_batch(workspace, provider=chain)
    assert chain.used_model == 'Groq fallback'
    assert len(workspace.topics) == 1
    assert any('Groq fallback' in message for message in workspace.feedback)
    first.generate.assert_called_once()
    second.generate.assert_called_once()
    third.generate.assert_not_called()


def test_primary_success_and_zero_success_do_not_fallback(workspace: Workspace) -> None:
    for result in [answer(workspace), GenerationResult(candidates=[], sufficiency_note='No supported new angles.')]:
        primary, first = attempt('Gemini primary', 'Gemini', result=result)
        fallback, second = attempt('Groq fallback', 'Groq', result=answer(workspace))
        chain = ProviderChain([primary, fallback])
        assert chain.generate('source prompt', 5) == result
        assert chain.used_model == 'Gemini primary'
        second.generate.assert_not_called()


def test_reserve_is_last_and_not_a_second_retry_loop(workspace: Workspace) -> None:
    primary, first = attempt('Gemini primary', 'Gemini', error=GenerationError('quota', 'Quota'))
    fallback, second = attempt('Groq fallback', 'Groq', error=GenerationError('timeout', 'Timeout'))
    reserve, third = attempt('Gemini reserve', 'Gemini', result=answer(workspace))
    chain = ProviderChain([primary, fallback, reserve])
    generate_topics(workspace, 5, chain)
    assert chain.used_model == 'Gemini reserve'
    assert [provider.generate.call_count for provider in [first, second, third]] == [1, 1, 1]


def test_all_failure_preserves_workspace_and_hides_raw_errors(workspace: Workspace) -> None:
    configure_plan(workspace, name='Open', mode='Campaign', guidance='Retain my brief')
    before = workspace.model_dump()
    primary, _ = attempt('Gemini primary', 'Gemini', error=GenerationError('provider', 'PRIVATE-KEY-SENTINEL'))
    fallback, _ = attempt('Groq fallback', 'Groq', error=GenerationError('quota', 'PRIVATE-SOURCE-SENTINEL'))
    with pytest.raises(GenerationError) as caught:
        generate_batch(workspace, provider=ProviderChain([primary, fallback]))
    assert 'PRIVATE' not in str(caught.value)
    assert workspace.model_dump() == before
    assert not workspace.busy


def test_invalid_credentials_skip_same_provider_reserve(workspace: Workspace) -> None:
    primary, _ = attempt('Gemini primary', 'Gemini', error=GenerationError('authentication', 'Bad key'))
    fallback, _ = attempt('Groq fallback', 'Groq', error=GenerationError('quota', 'Quota'))
    reserve, third = attempt('Gemini reserve', 'Gemini', result=answer(workspace))
    with pytest.raises(GenerationError):
        ProviderChain([primary, fallback, reserve]).generate('source', 5)
    third.generate.assert_not_called()


@pytest.mark.parametrize('category', ['blocked', 'validation'])
def test_refusal_or_evidence_rejection_does_not_trigger_provider_hopping(workspace: Workspace, category: str) -> None:
    primary, _ = attempt('Gemini primary', 'Gemini', error=GenerationError(category, 'Review evidence'))
    fallback, second = attempt('Groq fallback', 'Groq', result=answer(workspace))
    with pytest.raises(GenerationError) as caught:
        ProviderChain([primary, fallback]).generate('source', 5)
    assert caught.value.category == category
    second.generate.assert_not_called()


def test_real_local_evidence_failure_never_tries_a_second_model(workspace: Workspace) -> None:
    invalid = answer(workspace)
    invalid.candidates[0].core_insight = 'Ward 1 reports 9999 kg of sorted waste.'
    primary, _ = attempt('Gemini primary', 'Gemini', result=invalid)
    fallback, second = attempt('Groq fallback', 'Groq', result=answer(workspace))
    with pytest.raises(GenerationError) as caught:
        generate_batch(workspace, provider=ProviderChain([primary, fallback]))
    assert caught.value.category == 'validation'
    second.generate.assert_not_called()
    assert workspace.topics == []


def test_lazy_factory_failure_and_invalid_schema_can_fallback(workspace: Workspace) -> None:
    def missing_key():
        raise GenerationError('configuration', 'Missing key')
    fallback, provider = attempt('Groq fallback', 'Groq', result=answer(workspace))
    chain = ProviderChain([ProviderAttempt('Gemini primary', 'Gemini', missing_key), fallback])
    assert chain.generate('source', 5) == answer(workspace)
    malformed, _ = attempt('Gemini primary', 'Gemini', result={'wrong': 'shape'})
    assert ProviderChain([malformed, fallback]).generate('source', 5) == answer(workspace)


def test_configured_order_models_and_reserve_zero_retry(monkeypatch, workspace: Workspace) -> None:
    import ai.provider_chain as routes

    monkeypatch.setattr(settings, 'GEMINI_MODEL', 'gemini-3.6-flash')
    monkeypatch.setattr(settings, 'GEMINI_FALLBACK_MODEL', 'gemini-3.8-flash')
    monkeypatch.setattr(settings, 'GROQ_MODEL', 'openai/gpt-oss-120b')
    monkeypatch.setattr(settings, 'GEMINI_API_KEY', 'secret-one')
    monkeypatch.setattr(settings, 'GROQ_API_KEY', 'secret-two')
    failed = Mock()
    failed.generate.side_effect = GenerationError('provider', 'safe')
    worked = Mock()
    worked.generate.return_value = answer(workspace)
    gemini = Mock(side_effect=[failed, worked])
    groq = Mock(return_value=failed)
    monkeypatch.setattr(routes, 'GeminiClient', gemini)
    monkeypatch.setattr(routes, 'GroqClient', groq)
    chain = configured_chain()
    assert [route.family for route in chain.attempts] == ['Gemini', 'Groq', 'Gemini']
    generate_batch(workspace, provider=chain)
    assert gemini.call_args_list[0].args == ('secret-one', 'gemini-3.6-flash')
    assert groq.call_args.args == ('secret-two', 'openai/gpt-oss-120b')
    assert gemini.call_args_list[1].kwargs == {'retry_budget': 0}
    saved = save_workspace(workspace)
    assert b'secret-one' not in saved and b'secret-two' not in saved
    assert b'GROQ_API_KEY' not in saved


def response(result: GenerationResult, **updates) -> bytes:
    """Return a Groq-compatible JSON response envelope."""
    choice = {'finish_reason': 'stop', 'message': {'content': result.model_dump_json()}}
    choice.update(updates)
    return json.dumps({'choices': [choice]}).encode()


def test_groq_request_schema_headers_timeout_and_local_validation(workspace: Workspace) -> None:
    open_request = Mock(return_value=BytesIO(response(answer(workspace))))
    result = GroqClient('secret-two', 'openai/gpt-oss-120b', opener=open_request).generate('complete prompt', 5)
    assert result == answer(workspace)
    request = open_request.call_args.args[0]
    assert request.full_url == 'https://api.groq.com/openai/v1/chat/completions'
    assert request.get_header('Authorization') == 'Bearer secret-two'
    assert request.get_header('User-agent') == 'WasteAwarenessPlanner/1.0'
    assert open_request.call_args.kwargs['timeout'] == settings.API_TIMEOUT_SECONDS
    body = json.loads(request.data)
    assert body['model'] == 'openai/gpt-oss-120b'
    assert body['response_format']['json_schema']['strict'] is True
    assert body['messages'][0]['content'] == 'complete prompt'
    assert body['max_completion_tokens'] <= settings.GROQ_MAX_OUTPUT_TOKENS
    schema = wire_schema()
    assert 'title' in schema['$defs']['TopicCandidate']['properties']
    for record in [schema, *schema['$defs'].values()]:
        assert record['additionalProperties'] is False
        assert set(record['required']) == set(record['properties'])


@pytest.mark.parametrize('capacity', [0, 11, True, 1.5])
def test_groq_batch_bounds(capacity) -> None:
    opener = Mock()
    with pytest.raises(GenerationError):
        GroqClient('secret', 'openai/gpt-oss-120b', opener=opener).generate('source', capacity)
    opener.assert_not_called()


def test_groq_blocks_oversized_complete_context_without_transmission() -> None:
    opener = Mock()
    with pytest.raises(GenerationError) as caught:
        GroqClient('secret', 'openai/gpt-oss-120b', opener=opener).generate('ह' * 100_000, 10)
    assert caught.value.category == 'context'
    opener.assert_not_called()


@pytest.mark.parametrize('status,category', [
    (401, 'authentication'), (403, 'authentication'), (429, 'quota'), (404, 'model'),
    (413, 'context'), (400, 'request'), (422, 'request'), (500, 'provider'), (302, 'provider'),
])
def test_groq_sanitizes_http_errors_without_hidden_retries(status: int, category: str) -> None:
    failure = HTTPError('https://api.groq.com', status, 'PRIVATE-KEY-SENTINEL', {},
                        BytesIO(b'{"error":{"message":"PRIVATE-SOURCE-SENTINEL"}}'))
    opener = Mock(side_effect=failure)
    with pytest.raises(GenerationError) as caught:
        GroqClient('secret', 'openai/gpt-oss-120b', opener=opener).generate('source', 5)
    assert caught.value.category == category
    assert 'PRIVATE' not in str(caught.value)
    opener.assert_called_once()


@pytest.mark.parametrize('failure,category', [
    (TimeoutError('private'), 'timeout'), (URLError(TimeoutError('private')), 'timeout'),
    (URLError('private'), 'provider'),
])
def test_groq_sanitizes_network_errors(failure: Exception, category: str) -> None:
    with pytest.raises(GenerationError) as caught:
        GroqClient('secret', 'openai/gpt-oss-120b', opener=Mock(side_effect=failure)).generate('source', 5)
    assert caught.value.category == category
    assert 'private' not in str(caught.value)


@pytest.mark.parametrize('raw', [b'not JSON', b'{}', b'{"choices":[]}',
                               b'{"choices":[{"message":null}]}'])
def test_groq_invalid_envelopes(raw: bytes) -> None:
    with pytest.raises(GenerationError) as caught:
        GroqClient('secret', 'openai/gpt-oss-120b', opener=Mock(return_value=BytesIO(raw))).generate('source', 5)
    assert caught.value.category == 'invalid_output'


@pytest.mark.parametrize('finish,category', [('length', 'invalid_output'), ('content_filter', 'blocked')])
def test_groq_incomplete_and_refused_outputs(workspace: Workspace, finish: str, category: str) -> None:
    raw = response(answer(workspace), finish_reason=finish)
    with pytest.raises(GenerationError) as caught:
        GroqClient('secret', 'openai/gpt-oss-120b', opener=Mock(return_value=BytesIO(raw))).generate('source', 5)
    assert caught.value.category == category


def test_groq_response_size_and_no_redirect(monkeypatch) -> None:
    monkeypatch.setattr(settings, 'MAX_PROVIDER_RESPONSE_BYTES', 10)
    opener = Mock(return_value=BytesIO(b'x' * 11))
    with pytest.raises(GenerationError) as caught:
        GroqClient('secret', 'openai/gpt-oss-120b', opener=opener).generate('source', 5)
    assert caught.value.category == 'invalid_output'
    assert _NoRedirect().redirect_request(None, None, 302, '', {}, 'https://other.example') is None


def test_gemini_reserve_can_disable_extra_retry() -> None:
    from types import SimpleNamespace
    from tests.test_generation import FakeModels, APIProblem

    models = FakeModels(metadata_errors=[APIProblem(503)])
    sleep = Mock()
    client = GeminiClient('fake', 'reserve', sdk_client=SimpleNamespace(models=models),
                          sleep_fn=sleep, retry_budget=0)
    with pytest.raises(GenerationError):
        client.generate('source', 5)
    assert len(models.calls) == 1
    sleep.assert_not_called()
