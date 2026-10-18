"""Review evidence, obvious factual overreach and repeated angles locally.

These conservative checks are practical safeguards, not a semantic proof. Human
review is still necessary for relevance, factual proportionality and distinctness.
"""

from dataclasses import dataclass, field
from decimal import Decimal
import re
from typing import Iterable, TYPE_CHECKING

from config.settings import MAX_BATCH_TOPICS
from documents.evidence import source_passage
from models.generation_result import GenerationResult
from models.topic import TopicCandidate, TopicIdea
from workflow.topic_pool import is_repeated, normalize_text

if TYPE_CHECKING:
    from models.workspace import DocumentRecord

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "in", "is", "it", "of", "on", "or", "that", "the", "their", "this", "to", "was",
    "were", "with", "our", "can", "about", "into", "how", "why", "what", "your",
}
NUMBER_WORDS = dict(zip(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen "
    "fourteen fifteen sixteen seventeen eighteen nineteen".split(), range(20),
))
NUMBER_WORDS.update(dict(zip(
    "twenty thirty forty fifty sixty seventy eighty ninety".split(), range(20, 100, 10),
)))
NUMBER_WORDS.update(hundred=100, thousand=1000, million=1_000_000, billion=1_000_000_000)


@dataclass
class ValidatedBatch:
    """A candidate-only result; the workflow assigns IDs and mutates its own state."""

    candidates: list[TopicCandidate] = field(default_factory=list)
    feedback: list[str] = field(default_factory=list)
    sufficiency_note: str = ""


def _tokens(text: str) -> set[str]:
    return {word for word in normalize_text(text).split() if word not in STOP_WORDS}


def _numbers(text: str) -> set[str]:
    text = text.casefold().replace(",", "")
    text = re.sub(r"\bper\s+cent\b|\bpercent(?:age)?\b", "%", text)
    alternatives = "|".join(NUMBER_WORDS)
    pattern = rf"\b(?:{alternatives})(?:(?:[\s-]+(?:and[\s-]+)?)(?:{alternatives}))*\b"

    def replace_words(match: re.Match) -> str:
        group, total = 0, 0
        for word in re.findall(r"\w+", match.group()):
            if word == "and":
                continue
            number = NUMBER_WORDS[word]
            if number == 100:
                group = max(group, 1) * number
            elif number >= 1000:
                total += max(group, 1) * number
                group = 0
            else:
                group += number
        return str(total + group)

    text = re.sub(pattern, replace_words, text)
    numbers = set()
    for number in re.findall(r"\b\d+(?:\.\d+)?\s*%?", text):
        cleaned = number.strip()
        percentage = cleaned.endswith("%")
        value = Decimal(cleaned.rstrip("% "))
        normalized = format(value.normalize(), "f")
        numbers.add(normalized + ("%" if percentage else ""))
    return numbers


def validate_evidence(candidate: TopicCandidate, documents: Iterable["DocumentRecord"]) -> str:
    """Return a review reason when identity, location or excerpt is untraceable."""
    if not candidate.sources:
        return "no supporting source references were supplied"
    documents_by_id = {document.document_id: document for document in documents}
    for reference in candidate.sources:
        document = documents_by_id.get(reference.document_id)
        if document is None or reference.filename != document.filename:
            return "an evidence reference identifies an unknown source or incorrect filename"
        location_text = document.locations.get(reference.location)
        if location_text is None:
            return "an evidence reference uses a location absent from its source"
        if source_passage(reference.excerpt, location_text) is None:
            return "an evidence excerpt is not present at its cited source location"
    return ""


def review_candidate(
    candidate: TopicCandidate, documents: Iterable["DocumentRecord"],
    existing_topics: Iterable[TopicCandidate] = (), excluded_ids: Iterable[str] = (),
) -> list[str]:
    """Advisory checks only; a green result is not a proof of factual accuracy."""
    issues = []
    evidence_problem = validate_evidence(candidate, documents)
    if evidence_problem:
        issues.append(evidence_problem)
    claim_problem = _unsupported_claim(candidate)
    if claim_problem:
        issues.append(claim_problem)
    excluded = set(excluded_ids)
    duplicate = None
    for topic in existing_topics:
        if isinstance(candidate, TopicIdea) and candidate.topic_id == getattr(topic, "topic_id", None):
            continue
        if is_repeated(candidate, topic):
            duplicate = topic
            break
    if duplicate is not None:
        reason = "a previously excluded angle" if (
            getattr(duplicate, "topic_id", None) in excluded
        ) else "an existing or same-batch angle"
        issues.append(f"it repeats {reason}")
    return issues


def _restore_source_passages(candidate: TopicCandidate, documents: list["DocumentRecord"]) -> TopicCandidate:
    """Store original excerpts for matches; leave uncertain references for review."""
    restored = candidate.model_copy(deep=True)
    by_id = {document.document_id: document for document in documents}
    for reference in restored.sources:
        document = by_id.get(reference.document_id)
        if document is None or document.filename != reference.filename:
            continue
        text = document.locations.get(reference.location)
        if text is not None:
            passage = source_passage(reference.excerpt, text)
            if passage is not None and len(passage) <= 3000:
                reference.excerpt = passage
    unique = {}
    for reference in restored.sources:
        unique[(reference.document_id, reference.location, reference.excerpt)] = reference
    restored.sources = list(unique.values())
    return restored


def _unsupported_claim(candidate: TopicCandidate) -> str:
    evidence = "\n".join(reference.excerpt for reference in candidate.sources)
    claims = "\n".join((candidate.title, candidate.core_insight, candidate.context))
    if _numbers(claims) - _numbers(evidence):
        return "a numeric claim or percentage is absent from the cited excerpts"
    broader_scope = (
        "nationwide", "nationally", "globally", "worldwide", "across india", "all schools",
        "every school", "all households", "every household", "all cities", "every city",
    )
    for scope in broader_scope:
        if scope in claims.casefold() and scope not in evidence.casefold():
            return "a broader geographic or population claim is absent from the evidence"
    causal = re.compile(
        r"\b(causes?|caused|prevents?|prevented|reduces?|reduced|eliminates?|eliminated|"
        r"guarantees?|guaranteed|leads? to|results? in)\b", re.IGNORECASE
    )
    if causal.search(claims) and not causal.search(evidence):
        return "a causal effect or guaranteed outcome is not established by the cited excerpts"
    for unit_group in (
        {"kilogram", "kilograms", "kg"}, {"tonne", "tonnes", "ton", "tons"},
        {"rupee", "rupees", "inr", "₹"}, {"dollar", "dollars", "usd", "$"},
        {"litre", "litres", "liter", "liters"},
    ):
        claim_words = set(re.findall(r"\w+|[₹$]", claims.casefold()))
        evidence_words = set(re.findall(r"\w+|[₹$]", evidence.casefold()))
        if claim_words & unit_group and not evidence_words & unit_group:
            return "a unit or currency is absent from the cited excerpts"
    # Requiring some factual vocabulary catches an unrelated claim with a real quote.
    insight_words, evidence_words = _tokens(candidate.core_insight), _tokens(evidence)
    if insight_words and len(insight_words & evidence_words) / len(insight_words) < 0.20:
        return "the core insight has insufficient factual overlap with its cited evidence"
    context_words = _tokens(candidate.context)
    if len(candidate.context.split()) < 8 or (
        context_words and len(context_words & evidence_words) / len(context_words) < 0.15
    ):
        return "the supporting context is incomplete or insufficiently related to its cited evidence"
    return ""


def validate_candidates(
    result: GenerationResult,
    documents: Iterable["DocumentRecord"],
    existing_topics: Iterable[TopicIdea],
    excluded_ids: Iterable[str],
    capacity: int,
) -> ValidatedBatch:
    """Keep bounded readable candidates, attaching advisory feedback without mutation."""
    if isinstance(capacity, bool) or not 1 <= capacity <= MAX_BATCH_TOPICS:
        raise ValueError("The requested generation capacity must be between one and ten.")
    result = GenerationResult.model_validate(result)
    batch = ValidatedBatch(sufficiency_note=result.sufficiency_note)
    source_records = list(documents)
    previous = list(existing_topics)
    excluded = set(excluded_ids)
    for index, candidate in enumerate(result.candidates, start=1):
        label = f"Candidate {index}"
        issues = review_candidate(candidate, source_records, previous, excluded)
        if issues:
            batch.feedback.append(f"{label} kept for review: {'; '.join(issues)}.")
        batch.candidates.append(_restore_source_passages(candidate, source_records))
        previous.append(candidate)
    if batch.candidates:
        batch.feedback.append(
            "Topics are available for manual selection. Green means source checks passed; "
            "red means needs review. Local checks cannot prove correct reasoning."
        )
        if len(batch.candidates) > capacity:
            batch.feedback.append("The provider returned extra topics; all were kept in the review library.")
    else:
        batch.feedback.append("The provider returned no new topics; earlier work was preserved.")
    if len(batch.candidates) < capacity:
        batch.feedback.append(
            f"Accepted {len(batch.candidates)} of up to {capacity} requested topics; "
            "empty slots were not padded."
        )
    return batch
