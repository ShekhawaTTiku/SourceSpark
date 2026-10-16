"""A bounded explicit provider chain; it never runs on its own or weakens evidence checks."""

from dataclasses import dataclass
from typing import Any, Callable

from pydantic import ValidationError

from ai.gemini_client import GeminiClient, GenerationError
from ai.groq_client import GroqClient
from config import settings
from models.generation_result import GenerationResult


@dataclass(frozen=True)
class ProviderAttempt:
    """Keep only safe public labels and lazy factories; do not persist clients or keys."""

    label: str
    family: str
    factory: Callable[[], Any]


class ProviderChain:
    """Try each configured route once, retaining a safe explanation of the route used."""

    def __init__(self, attempts: list[ProviderAttempt]) -> None:
        self.attempts = attempts
        self.feedback: list[str] = []
        self.used_model: str | None = None

    def generate(self, prompt: str, capacity: int) -> GenerationResult:
        """Fail over only for operational/schema failures, not refusals or weak evidence."""
        self.feedback = []
        self.used_model = None
        last_error: GenerationError | None = None
        unavailable_families: set[str] = set()
        for attempt in self.attempts:
            if attempt.family in unavailable_families:
                self.feedback.append(f'Skipped {attempt.label}: this provider has no valid credentials.')
                continue
            try:
                provider = attempt.factory()
                result = GenerationResult.model_validate(provider.generate(prompt, capacity))
            except ValidationError:
                last_error = GenerationError('invalid_output', 'The provider returned invalid structured data.', True)
            except GenerationError as error:
                if error.category in {'blocked', 'validation'}:
                    # An alternate provider must not bypass a refusal or local evidence rejection.
                    raise
                last_error = error
                if error.category in {'authentication', 'configuration'}:
                    unavailable_families.add(attempt.family)
            else:
                self.used_model = attempt.label
                self.feedback.append(f'Generated with {attempt.label}.')
                return result
            self.feedback.append(f'{attempt.label} unavailable ({last_error.category}).')
        if last_error is None:
            raise GenerationError('configuration', 'No generation provider is configured. Add the API keys in .env.')
        reasons = ' '.join(self.feedback)
        raise GenerationError(
            last_error.category,
            f'All configured generation routes failed. {reasons} '
            'Your workspace is intact. Check the API keys, model access, quotas or connection and retry.',
            last_error.retryable,
        ) from None


def configured_chain() -> ProviderChain:
    """Primary Gemini, direct Groq fallback, then alternate Gemini reserve, in that order."""
    attempts = [
        ProviderAttempt(
            f'Gemini / {settings.GEMINI_MODEL}', 'Gemini',
            lambda: GeminiClient(settings.GEMINI_API_KEY, settings.GEMINI_MODEL),
        ),
        ProviderAttempt(
            f'Groq / {settings.GROQ_MODEL}', 'Groq',
            lambda: GroqClient(settings.GROQ_API_KEY, settings.GROQ_MODEL),
        ),
    ]
    if (settings.GEMINI_FALLBACK_MODEL
            and settings.GEMINI_FALLBACK_MODEL != settings.GEMINI_MODEL):
        attempts.append(ProviderAttempt(
            f'Gemini / {settings.GEMINI_FALLBACK_MODEL}', 'Gemini',
            lambda: GeminiClient(
                settings.GEMINI_API_KEY, settings.GEMINI_FALLBACK_MODEL, retry_budget=0,
            ),
        ))
    return ProviderChain(attempts)
