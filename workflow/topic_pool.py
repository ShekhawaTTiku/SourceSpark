"""Practical repeated-angle checks without a global topic-count ceiling."""

from difflib import SequenceMatcher
import re
import unicodedata

from models.topic import TopicCandidate, TopicIdea


def normalize_text(value: str) -> str:
    """Normalize case, Unicode, punctuation, and spacing for comparison."""
    normalized = unicodedata.normalize('NFKC', value).casefold()
    return ' '.join(re.findall(r'\w+', normalized))


def is_repeated(candidate: TopicCandidate, existing: TopicCandidate) -> bool:
    """Catch exact/close wording; shared evidence alone never proves duplication."""
    title, old_title = normalize_text(candidate.title), normalize_text(existing.title)
    insight, old_insight = normalize_text(candidate.core_insight), normalize_text(existing.core_insight)
    if title == old_title or insight == old_insight:
        return True
    title_ratio = SequenceMatcher(None, title, old_title).ratio()
    insight_ratio = SequenceMatcher(None, insight, old_insight).ratio()
    # Very similar templates with distinct measured values may describe distinct observations.
    numbers = re.findall(r'\d+(?:\.\d+)?', insight)
    old_numbers = re.findall(r'\d+(?:\.\d+)?', old_insight)
    if numbers != old_numbers:
        return False
    return insight_ratio >= 0.93 or (title_ratio >= 0.90 and insight_ratio >= 0.80)


def accept_topics(
    topics: list[TopicIdea], candidates: list[TopicCandidate], capacity: int = 10,
) -> tuple[list[TopicIdea], list[str]]:
    """Return independent accepted records and feedback, bounded by request capacity."""
    from config.settings import MAX_BATCH_TOPICS

    if not 1 <= capacity <= MAX_BATCH_TOPICS:
        raise ValueError('A generation batch must contain at most ten candidates.')
    accepted: list[TopicIdea] = []
    feedback: list[str] = []
    for candidate in candidates:
        if len(accepted) >= capacity:
            feedback.append('Rejected candidate beyond the requested batch capacity.')
        else:
            accepted.append(TopicIdea(**candidate.model_dump()))
    return accepted, feedback
