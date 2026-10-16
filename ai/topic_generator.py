"""Prepare, call and validate generation without owning mutable workspace state."""

from typing import Protocol, TYPE_CHECKING

from pydantic import ValidationError

from ai.gemini_client import GenerationError
from ai.provider_chain import configured_chain
from ai.response_validator import ValidatedBatch, validate_candidates
from models.generation_result import GenerationResult
from prompts.builder import build_request
from workflow.topic_pool import normalize_text

if TYPE_CHECKING:
    from models.workspace import Workspace


class TopicProvider(Protocol):
    def generate(self, prompt: str, capacity: int) -> GenerationResult:
        """Return a structured response or a sanitized generation error."""


def _brief_relevance_feedback(workspace: "Workspace", batch: ValidatedBatch) -> None:
    """Flag uncertain wording matches without treating word overlap as semantic proof."""
    generic = {
        "a", "an", "the", "and", "or", "to", "of", "for", "in", "on", "with",
        "explain", "understand", "communicate", "awareness", "use", "make", "help",
    }
    audience = set(normalize_text(workspace.plan.audience).split()) - generic
    goal = set(normalize_text(workspace.plan.goal).split()) - generic
    for index, candidate in enumerate(batch.candidates, start=1):
        audience_words = set(normalize_text(candidate.target_audience).split())
        angle_words = set(normalize_text(
            f"{candidate.title} {candidate.core_insight} {candidate.context}"
        ).split())
        if audience and not audience & audience_words:
            batch.feedback.append(
                f"Accepted candidate {index} needs brief review: the suggested audience wording "
                "differs from the requested audience. Local word matching cannot establish relevance."
            )
        if goal and not goal & angle_words:
            batch.feedback.append(
                f"Accepted candidate {index} needs brief review: the communication goal has no "
                "direct wording match with the supported angle. Check relevance before finalizing."
            )


def generate_topics(
    workspace: "Workspace", capacity: int, provider: TopicProvider | None = None
) -> ValidatedBatch:
    """Return accepted candidates and feedback; the coordinator performs the merge."""
    try:
        prompt = build_request(workspace, capacity)
    except ValueError as error:
        raise GenerationError("context", str(error), retryable=False) from None
    selected_provider = provider or configured_chain()
    try:
        result = selected_provider.generate(prompt, capacity)
        result = GenerationResult.model_validate(result)
    except ValidationError:
        raise GenerationError(
            "invalid_output", "The provider response was incomplete or invalid. You can retry.",
            retryable=True,
        ) from None
    batch = validate_candidates(
        result, workspace.documents, workspace.topics, workspace.excluded_topic_ids, capacity
    )
    # Only safe route labels enter feedback; credentials and clients stay outside workspace data.
    batch.feedback = [*getattr(selected_provider, "feedback", []), *batch.feedback]
    if result.candidates and not batch.candidates:
        raise GenerationError(
            "validation", "No returned candidate passed validation. " + " ".join(batch.feedback[:10]),
            retryable=True,
        )
    _brief_relevance_feedback(workspace, batch)
    return batch
