"""Groq structured-output adapter using the standard library, with no hidden retries."""

import json
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pydantic import ValidationError

from ai.gemini_client import GenerationError
from config import settings
from models.generation_result import GenerationResult


class _NoRedirect(HTTPRedirectHandler):
    """Do not forward an Authorization header to another URL on a redirect."""

    def redirect_request(
        self, req: Request, fp: Any, code: int, msg: str, headers: Any, newurl: str,
    ) -> None:
        return None


def wire_schema() -> dict[str, Any]:
    """Use Groq's supported strict structural schema; enforce lengths locally afterwards."""
    schema = GenerationResult.model_json_schema()

    def clean(value: Any) -> Any:
        if isinstance(value, dict):
            # String/array length and regex constraints are checked by local Pydantic.
            result = {}
            for key, item in value.items():
                if key in {'minLength', 'maxLength', 'minItems', 'maxItems', 'pattern', 'title'}:
                    continue
                if key in {'properties', '$defs'}:
                    # Property names such as "title" are data, not schema annotations.
                    result[key] = {name: clean(schema) for name, schema in item.items()}
                else:
                    result[key] = clean(item)
            if result.get('type') == 'object':
                result['additionalProperties'] = False
                result['required'] = list(result.get('properties', {}))
            return result
        if isinstance(value, list):
            return [clean(item) for item in value]
        return value

    return clean(schema)


class GroqClient:
    """One bounded HTTPS attempt. The provider chain, not this adapter, owns fallback."""

    def __init__(
        self, key: str, model: str, *, opener: Callable[..., Any] | None = None,
    ) -> None:
        if not key or not key.strip():
            raise GenerationError('configuration', 'Set GROQ_API_KEY to enable the Groq fallback.')
        if model != 'openai/gpt-oss-120b':
            raise GenerationError(
                'model', 'This Groq adapter is verified for openai/gpt-oss-120b. Check GROQ_MODEL.'
            )
        self._key = key.strip()
        self.model = model
        self._open = opener or build_opener(_NoRedirect()).open

    def generate(self, prompt: str, capacity: int) -> GenerationResult:
        """Submit the complete prompt or reject it; never shorten its sources/angle history."""
        if type(capacity) is not int or not 1 <= capacity <= settings.MAX_BATCH_TOPICS:
            raise GenerationError('request', 'Generation capacity must be between one and ten.')
        schema = wire_schema()
        response_allowance = max(4096, capacity * 1400 + 1024)
        # GPT-OSS uses a byte-level tokenizer. UTF-8 bytes plus framing bound tokens
        # conservatively, unlike a characters/4 guess; oversized requests are blocked.
        input_upper_bound = len(prompt.encode('utf-8')) + len(
            json.dumps(schema, ensure_ascii=False).encode('utf-8')
        ) + 1024
        if (input_upper_bound + response_allowance > settings.GROQ_CONTEXT_TOKENS
                or response_allowance > settings.GROQ_MAX_OUTPUT_TOKENS):
            raise GenerationError(
                'context', 'The full request does not safely fit the Groq model context. '
                'Nothing was truncated; use smaller sources or the Gemini reserve.'
            )
        payload = {
            'model': self.model, 'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.2, 'max_completion_tokens': response_allowance,
            'response_format': {'type': 'json_schema', 'json_schema': {
                'name': 'campaign_topic_batch', 'strict': True, 'schema': schema,
            }},
        }
        request = Request(
            'https://api.groq.com/openai/v1/chat/completions',
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {self._key}', 'Content-Type': 'application/json',
                'Accept': 'application/json', 'User-Agent': 'WasteAwarenessPlanner/1.0',
            },
            method='POST',
        )
        try:
            with self._open(request, timeout=settings.API_TIMEOUT_SECONDS) as response:
                data = response.read(settings.MAX_PROVIDER_RESPONSE_BYTES + 1)
        except HTTPError as error:
            self._raise_http_error(error)
        except (TimeoutError, URLError, OSError) as error:
            reason = getattr(error, 'reason', error)
            if isinstance(reason, TimeoutError) or 'timeout' in type(reason).__name__.lower():
                raise GenerationError('timeout', 'The Groq request timed out; your work is intact.', True) from None
            raise GenerationError('provider', 'Groq could not be reached; your work is intact.', True) from None
        if len(data) > settings.MAX_PROVIDER_RESPONSE_BYTES:
            raise GenerationError('invalid_output', 'Groq returned an oversized response.', True)
        try:
            body = json.loads(data)
            choice = body['choices'][0]
            message = choice['message']
            if message.get('refusal') or choice.get('finish_reason') == 'content_filter':
                raise GenerationError('blocked', 'Groq declined this request. Review the sources or brief.')
            if choice.get('finish_reason') != 'stop':
                raise GenerationError('invalid_output', 'Groq did not finish its structured response.', True)
            content = message['content']
            if not isinstance(content, str):
                raise ValueError('Missing structured response')
            return GenerationResult.model_validate_json(content)
        except (ValueError, KeyError, IndexError, TypeError, AttributeError,
                RecursionError, ValidationError):
            raise GenerationError('invalid_output', 'Groq returned incomplete or invalid structured data.', True) from None

    @staticmethod
    def _raise_http_error(error: HTTPError) -> None:
        """Classify safe categories without surfacing request headers or raw error text."""
        try:
            raw = error.read(16_384)
            detail = json.loads(raw).get('error', {})
            reason = str(detail.get('code', '')).lower() if isinstance(detail, dict) else ''
        except (ValueError, TypeError, AttributeError, OSError):
            reason = ''
        finally:
            error.close()
        if reason in {'content_policy_violation', 'content_filter', 'safety_violation'}:
            raise GenerationError('blocked', 'Groq declined this request. Review the sources or brief.') from None
        if error.code in {401, 403}:
            raise GenerationError('authentication', 'Groq rejected access. Check GROQ_API_KEY and account permissions.') from None
        if error.code == 429:
            raise GenerationError('quota', 'Groq quota or rate limit reached. Check account limits.', True) from None
        if error.code == 404:
            raise GenerationError('model', 'The Groq model is unavailable to this account.') from None
        if error.code == 413 or reason == 'context_length_exceeded':
            raise GenerationError('context', 'The complete request exceeds Groq context limits; nothing was truncated.') from None
        if error.code in {400, 422}:
            raise GenerationError('request', 'Groq rejected the request or schema. Check model compatibility.') from None
        raise GenerationError('provider', 'Groq could not complete this request; your work is intact.', True) from None
