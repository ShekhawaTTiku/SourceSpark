"""Evidence/recovery tests use fictional records and mocked provider calls only."""

import hashlib
from types import SimpleNamespace

import pytest

from ai.gemini_client import GeminiClient, GenerationError
from ai.response_validator import review_candidate, validate_candidates
from ai.topic_generator import generate_topics
from documents.extraction import canonical_content
from models.generation_result import GenerationResult
from models.topic import EvidenceReference, TopicCandidate, TopicIdea
from models.workspace import DocumentRecord, Workspace


def source() -> DocumentRecord:
    locations = {
        "Paragraph 1": "Greenfield School has 20 classrooms. Eight classrooms lack bin labels.",
        "Paragraph 2": "The school noticeboard displays collection information for students.",
    }
    return DocumentRecord(
        document_id=hashlib.sha256(b"fictional school report").hexdigest(),
        filename="school.docx", file_type="docx", size_bytes=100,
        locations=locations, content=canonical_content(locations),
    )


def candidate(**updates) -> TopicCandidate:
    document = source()
    fields = dict(
        title="Classroom bin labels need attention",
        core_insight="Eight classrooms at Greenfield School lack bin labels.",
        context="The school report identifies missing bin labels in eight classrooms. "
                "A school-focused topic can explain this documented label gap.",
        target_audience="School students", suggested_format="Poster",
        sources=[EvidenceReference(
            document_id=document.document_id, filename=document.filename,
            location="Paragraph 1", excerpt=document.locations["Paragraph 1"],
        )],
    )
    fields.update(updates)
    return TopicCandidate(**fields)


def result(*candidates) -> GenerationResult:
    return GenerationResult(candidates=list(candidates), sufficiency_note="Only documented angles are included.")


def test_supported_candidate_is_independent_and_preserves_complete_context():
    proposed = candidate()
    batch = validate_candidates(result(proposed), [source()], [], [], 5)
    assert len(batch.candidates) == 1
    assert batch.candidates[0].context == proposed.context
    assert batch.candidates[0] is not proposed
    assert any("cannot prove" in message for message in batch.feedback)


def test_short_or_generic_context_is_kept_with_review_note():
    for context in (
        "A brief note.",
        "An important school awareness topic.",
        "A compelling communication strategy provides actionable background for persuasive messaging.",
    ):
        batch = validate_candidates(result(candidate(context=context)), [source()], [], [], 5)
        assert len(batch.candidates) == 1
        assert any("supporting context" in message for message in batch.feedback)


@pytest.mark.parametrize("field,value", [
    ("document_id", "f" * 64), ("filename", "invented.docx"),
    ("location", "Page 999"), ("excerpt", "An invented supporting statement."),
])
def test_untraceable_evidence_is_kept_with_review_note(field, value):
    proposed = candidate()
    proposed.sources[0] = proposed.sources[0].model_copy(update={field: value})
    batch = validate_candidates(result(proposed), [source()], [], [], 5)
    assert len(batch.candidates) == 1
    assert any("kept for review" in message for message in batch.feedback)
    assert review_candidate(batch.candidates[0], [source()])


@pytest.mark.parametrize("updates,reason", [
    ({"core_insight": "Ninety classrooms at Greenfield School lack bin labels."}, "numeric"),
    ({"core_insight": "80% of Greenfield School classrooms lack bin labels."}, "numeric"),
    ({"context": "The school report proves all schools have missing bin labels."}, "broader"),
    ({"context": "Missing school bin labels causes student littering throughout the school."}, "causal"),
    ({"core_insight": "Eight kilograms of labels are missing from the school."}, "unit"),
    ({"core_insight": "Ocean currents circulate plastic around distant marine habitats."}, "overlap"),
])
def test_unsupported_claims_are_kept_with_review_note(updates, reason):
    batch = validate_candidates(result(candidate(**updates)), [source()], [], [], 5)
    assert len(batch.candidates) == 1
    assert any(reason in message for message in batch.feedback)


def test_repeats_within_batch_and_excluded_angles_are_kept_with_review_note():
    existing = TopicIdea(**candidate().model_dump())
    batch = validate_candidates(result(candidate()), [source()], [existing], [existing.topic_id], 5)
    assert len(batch.candidates) == 1
    assert any("excluded" in message for message in batch.feedback)
    batch = validate_candidates(result(candidate(), candidate()), [source()], [], [], 5)
    assert len(batch.candidates) == 2
    assert any("same-batch" in message for message in batch.feedback)


def test_near_duplicate_wording_is_kept_for_review():
    existing = TopicIdea(**candidate().model_dump())
    proposed = candidate(
        title="Classroom bin labels need attention!",
        core_insight="Eight classrooms at Greenfield School lack their bin labels.",
    )
    batch = validate_candidates(result(proposed), [source()], [existing], [], 5)
    assert len(batch.candidates) == 1
    assert any("repeats" in message for message in batch.feedback)


def test_distinct_angles_can_share_the_same_source():
    other = candidate(
        title="Find collection information on the noticeboard",
        core_insight="The school noticeboard displays collection information for students.",
        context="Students can find collection information on the school noticeboard. "
                "This topic explains where the report says that information appears.",
        sources=[EvidenceReference(
            document_id=source().document_id, filename="school.docx", location="Paragraph 2",
            excerpt=source().locations["Paragraph 2"],
        )],
    )
    batch = validate_candidates(result(candidate(), other), [source()], [], [], 5)
    assert len(batch.candidates) == 2


def test_extra_returned_candidates_are_kept_in_review_library():
    other = candidate(title="The school's reported classroom count",
        core_insight="Greenfield School has 20 classrooms in its school report.",
        context="The school report records 20 classrooms at Greenfield School. "
                "The topic explains the documented scope of the classroom report.")
    batch = validate_candidates(result(candidate(), other), [source()], [], [], 1)
    assert len(batch.candidates) == 2
    assert any("extra topics" in message for message in batch.feedback)


def test_short_and_zero_results_are_valid_successes():
    for proposed in (result(), result(candidate())):
        batch = validate_candidates(proposed, [source()], [], [], 5)
        assert len(batch.candidates) == len(proposed.candidates)
        assert batch.sufficiency_note
        assert any("not padded" in message for message in batch.feedback)


class FakeProvider:
    def __init__(self, answer=None, error=None):
        self.answer = answer
        self.error = error
        self.calls = []

    def generate(self, prompt, capacity):
        self.calls.append((prompt, capacity))
        if self.error:
            raise self.error
        return self.answer


def test_generator_is_injected_and_does_not_mutate_workspace():
    workspace = Workspace(documents=[source()])
    before = workspace.model_dump(mode="json")
    provider = FakeProvider(result(candidate()))
    batch = generate_topics(workspace, 5, provider)
    assert len(provider.calls) == 1
    assert len(batch.candidates) == 1
    assert workspace.model_dump(mode="json") == before


def test_uncertain_brief_relevance_is_flagged_for_human_review():
    workspace = Workspace(documents=[source()])
    workspace.plan.audience = "Hospital administrators"
    workspace.plan.goal = "Describe collection route fuel consumption"
    batch = generate_topics(workspace, 5, FakeProvider(result(candidate())))
    assert len(batch.candidates) == 1
    assert any("audience wording" in message for message in batch.feedback)
    assert any("communication goal" in message for message in batch.feedback)


def test_provider_failure_does_not_mutate_prior_work():
    workspace = Workspace(documents=[source()], topics=[TopicIdea(**candidate().model_dump())])
    before = workspace.model_dump(mode="json")
    provider = FakeProvider(error=GenerationError("timeout", "Safe timeout", True))
    with pytest.raises(GenerationError) as caught:
        generate_topics(workspace, 5, provider)
    assert caught.value.category == "timeout"
    assert workspace.model_dump(mode="json") == before


def test_invalid_provider_schema_is_a_distinct_failure():
    with pytest.raises(GenerationError) as caught:
        generate_topics(Workspace(documents=[source()]), 5, FakeProvider({"wrong": "shape"}))
    assert caught.value.category == "invalid_output"


def test_all_flagged_candidates_are_success_without_repair_call_and_zero_is_success():
    workspace = Workspace(documents=[source()])
    invalid = candidate(core_insight="Ninety classrooms at Greenfield School lack bin labels.")
    provider = FakeProvider(result(invalid))
    batch = generate_topics(workspace, 5, provider)
    assert len(batch.candidates) == 1
    assert any("numeric" in message for message in batch.feedback)
    assert len(provider.calls) == 1
    assert not generate_topics(workspace, 5, FakeProvider(result())).candidates


def test_spelled_numbers_match_equivalent_digits():
    proposed = candidate(core_insight="8 classrooms at Greenfield School lack bin labels.")
    assert validate_candidates(result(proposed), [source()], [], [], 5).candidates


def test_percentage_decimals_match_but_plain_counts_do_not_become_percentages():
    document = source()
    document.locations = {"Paragraph 1": "The school report records 12% of bins without labels."}
    document.content = canonical_content(document.locations)
    proposed = candidate(
        title="Reported share of bins missing labels",
        core_insight="The school report records 12.0% of bins without labels.",
        context="The school report records the share of bins without labels as 12 percent.",
        sources=[EvidenceReference(document_id=document.document_id, filename=document.filename,
            location="Paragraph 1", excerpt=document.locations["Paragraph 1"])],
    )
    assert validate_candidates(result(proposed), [document], [], [], 5).candidates
    document.locations = {"Paragraph 1": "The school report records 12 bins without labels."}
    document.content = canonical_content(document.locations)
    proposed.sources[0].excerpt = document.locations["Paragraph 1"]
    batch = validate_candidates(result(proposed), [document], [], [], 5)
    assert len(batch.candidates) == 1
    assert any("numeric" in message for message in batch.feedback)


class APIProblem(Exception):
    def __init__(self, code, details=None, retry_after=None):
        super().__init__("PRIVATE raw provider text with key and source material")
        self.code = code
        self.response_json = {"error": {"details": details or []}}
        self.response = SimpleNamespace(headers={"Retry-After": retry_after} if retry_after else {})


class FakeModels:
    def __init__(self, response=None, generate_errors=None, input_limit=100_000,
                 output_limit=20_000, token_count=1000, metadata_errors=None):
        self.response = response or SimpleNamespace(parsed=result(candidate()), candidates=[])
        self.generate_errors = list(generate_errors or [])
        self.metadata_errors = list(metadata_errors or [])
        self.input_limit, self.output_limit, self.token_count = input_limit, output_limit, token_count
        self.calls = []

    def get(self, **kwargs):
        self.calls.append(("metadata", kwargs))
        if self.metadata_errors:
            raise self.metadata_errors.pop(0)
        return SimpleNamespace(name="models/account-model", input_token_limit=self.input_limit,
            output_token_limit=self.output_limit, supported_actions=["generateContent"])

    def count_tokens(self, **kwargs):
        self.calls.append(("tokens", kwargs))
        return SimpleNamespace(total_tokens=self.token_count)

    def generate_content(self, **kwargs):
        self.calls.append(("generate", kwargs))
        if self.generate_errors:
            raise self.generate_errors.pop(0)
        return self.response


def gemini(models):
    sleeps = []
    client = GeminiClient("fictional-test-key", "account-model", sdk_client=SimpleNamespace(models=models),
        sleep_fn=sleeps.append)
    return client, sleeps


def test_gemini_counts_full_prompt_and_schema_before_generating():
    models = FakeModels()
    client, _ = gemini(models)
    response = client.generate("Complete source and remembered angles", 5)
    assert len(response.candidates) == 1
    assert [call[0] for call in models.calls] == ["metadata", "tokens", "generate"]
    assert "Complete source and remembered angles" in models.calls[1][1]["contents"]
    assert "Output schema" in models.calls[1][1]["contents"]
    assert client.last_metadata["response_allowance"] > 0
    config = models.calls[2][1]["config"]
    from ai.gemini_client import gemini_schema
    assert config.response_schema == gemini_schema()
    assert 'title' in config.response_schema['properties']['candidates']['items']['properties']


@pytest.mark.parametrize("kwargs", [
    {"input_limit": 5000, "token_count": 2000}, {"output_limit": 1000},
])
def test_token_or_output_budget_block_before_generation(kwargs):
    models = FakeModels(**kwargs)
    client, _ = gemini(models)
    with pytest.raises(GenerationError) as caught:
        client.generate("complete prompt", 5)
    assert caught.value.category == "context"
    assert not any(call[0] == "generate" for call in models.calls)


def test_temporary_error_retries_once_and_honors_retry_guidance():
    models = FakeModels(generate_errors=[APIProblem(503, retry_after="2")])
    client, sleeps = gemini(models)
    assert client.generate("complete prompt", 5).candidates
    assert sleeps == [2.0]
    assert sum(call[0] == "generate" for call in models.calls) == 2


def test_retry_budget_is_shared_across_metadata_and_generation():
    models = FakeModels(metadata_errors=[APIProblem(503)], generate_errors=[APIProblem(503)])
    client, sleeps = gemini(models)
    with pytest.raises(GenerationError) as caught:
        client.generate("complete prompt", 5)
    assert caught.value.category == "provider"
    assert len(sleeps) == 1
    assert sum(call[0] == "generate" for call in models.calls) == 1
    assert "PRIVATE" not in str(caught.value)


@pytest.mark.parametrize("code,category", [(401, "authentication"), (403, "authentication"),
    (404, "model"), (400, "request"), (429, "quota")])
def test_nonrecoverable_failures_are_not_blindly_retried(code, category):
    models = FakeModels(generate_errors=[APIProblem(code)])
    client, sleeps = gemini(models)
    with pytest.raises(GenerationError) as caught:
        client.generate("complete prompt", 5)
    assert caught.value.category == category
    assert sleeps == []
    assert "PRIVATE" not in str(caught.value)


def test_invalid_api_key_reason_is_distinguished_from_other_bad_requests():
    details = [{"@type": "type.googleapis.com/google.rpc.ErrorInfo", "reason": "API_KEY_INVALID"}]
    client, sleeps = gemini(FakeModels(generate_errors=[APIProblem(400, details)]))
    with pytest.raises(GenerationError) as caught:
        client.generate("complete prompt", 5)
    assert caught.value.category == "authentication"
    assert not sleeps


def test_sdk_transport_uses_bounded_timeout_and_disables_hidden_retries(monkeypatch):
    from google import genai
    created = {}
    closed = []

    def create_client(**kwargs):
        created.update(kwargs)
        return SimpleNamespace(models=FakeModels(), close=lambda: closed.append(True))

    monkeypatch.setattr(genai, "Client", create_client)
    client = GeminiClient("fictional-test-key", "account-model")
    client.generate("complete prompt", 1)
    assert created["http_options"].timeout == 60_000
    assert created["http_options"].retry_options.attempts == 1
    assert closed == [True]


def test_retry_info_and_daily_quota_are_distinguished():
    retry_info = {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "3s"}
    models = FakeModels(generate_errors=[APIProblem(429, [retry_info])])
    client, sleeps = gemini(models)
    client.generate("complete prompt", 5)
    assert sleeps == [3.0]
    quota = {"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": [{"quotaId": "RequestsPerDay"}]}
    client, sleeps = gemini(FakeModels(generate_errors=[APIProblem(429, [retry_info, quota])]))
    with pytest.raises(GenerationError) as caught:
        client.generate("complete prompt", 5)
    assert caught.value.category == "quota"
    assert not caught.value.retryable
    assert sleeps == []


def test_long_retry_guidance_is_respected_without_blocking_sleep():
    client, sleeps = gemini(FakeModels(generate_errors=[APIProblem(503, retry_after="120")]))
    with pytest.raises(GenerationError, match="120"):
        client.generate("complete prompt", 5)
    assert sleeps == []


def test_timeout_is_distinct_and_requires_manual_retry():
    client, sleeps = gemini(FakeModels(generate_errors=[TimeoutError("PRIVATE details")]))
    with pytest.raises(GenerationError) as caught:
        client.generate("complete prompt", 5)
    assert caught.value.category == "timeout"
    assert caught.value.retryable
    assert sleeps == []


@pytest.mark.parametrize("response", [
    SimpleNamespace(parsed=None, text="not JSON", candidates=[]),
    SimpleNamespace(parsed={"wrong": "shape"}, candidates=[]),
    SimpleNamespace(parsed=None, candidates=[SimpleNamespace(finish_reason="MAX_TOKENS")]),
])
def test_invalid_or_incomplete_model_outputs_are_distinct(response):
    client, sleeps = gemini(FakeModels(response=response))
    with pytest.raises(GenerationError) as caught:
        client.generate("complete prompt", 5)
    assert caught.value.category == "invalid_output"
    assert sleeps == []


def test_empty_response_retries_once_then_raises_invalid_output():
    # An empty body (text=None, parsed=None) is a transient load-spike pattern; the
    # shared retry budget allows exactly one automatic re-attempt before giving up.
    empty = SimpleNamespace(parsed=None, text=None, candidates=[])
    client, sleeps = gemini(FakeModels(response=empty))
    with pytest.raises(GenerationError) as caught:
        client.generate("complete prompt", 5)
    assert caught.value.category == "invalid_output"
    assert sleeps == [1.0]  # One 1-second pause before the retry attempt


def test_configuration_is_required_without_network_calls():
    for key, model in [("", "model"), ("key", "")]:
        with pytest.raises(GenerationError) as caught:
            GeminiClient(key, model)
        assert caught.value.category == "configuration"
