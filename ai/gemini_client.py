"""Bounded Google GenAI access with sanitized, actionable error categories.

No configured model is assumed free or available. Model metadata and complete
request tokens are checked at request time. Account quotas and live factual
quality still require verification with the user's own configured account.
"""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import re
import time
from typing import Any, Callable

from pydantic import ValidationError

from config.settings import API_TIMEOUT_SECONDS, MAX_API_RETRIES, MAX_BATCH_TOPICS
from models.generation_result import GenerationResult


class GenerationError(RuntimeError):
    """A public-safe failure; raw provider messages and responses stay private."""

    def __init__(self, category: str, message: str, retryable: bool = False):
        super().__init__(message)
        self.category = category
        self.retryable = retryable


def gemini_schema() -> dict[str, Any]:
    """Inline the supported structural schema; retain strict constraints locally."""
    original = GenerationResult.model_json_schema()
    definitions = original.get("$defs", {})

    def convert(node: dict[str, Any]) -> dict[str, Any]:
        if "$ref" in node:
            return convert(definitions[node["$ref"].split("/")[-1]])
        output = {}
        for key in ("type", "description", "enum", "required"):
            if key in node:
                output[key] = node[key]
        if "properties" in node:
            output["properties"] = {name: convert(item)
                                    for name, item in node["properties"].items()}
        if "items" in node:
            output["items"] = convert(node["items"])
        return output

    return convert(original)


def _error_code(error: Exception) -> int | None:
    code = getattr(error, "code", None) or getattr(error, "status_code", None)
    if not isinstance(code, int):
        response = getattr(error, "response", None)
        code = getattr(response, "status_code", None)
    return code if isinstance(code, int) else None


def _error_details(error: Exception) -> list[dict]:
    payload = getattr(error, "response_json", None)
    if isinstance(payload, dict):
        body = payload.get("error", payload)
        if isinstance(body, dict) and isinstance(body.get("details"), list):
            return [detail for detail in body["details"] if isinstance(detail, dict)]
    details = getattr(error, "details", None)
    return [detail for detail in details if isinstance(detail, dict)] if isinstance(details, list) else []


def _retry_delay(error: Exception) -> float | None:
    """Read Retry-After or Google's RetryInfo without exposing its raw payload."""
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", {}) or {}
    header = headers.get("retry-after") or headers.get("Retry-After")
    if header:
        try:
            return max(0.0, float(header))
        except (TypeError, ValueError):
            try:
                retry_time = parsedate_to_datetime(str(header))
                if retry_time.tzinfo is None:
                    retry_time = retry_time.replace(tzinfo=timezone.utc)
                return max(0.0, (retry_time - datetime.now(timezone.utc)).total_seconds())
            except (TypeError, ValueError, OverflowError):
                return None
    for detail in _error_details(error):
        if str(detail.get("@type", "")).endswith("RetryInfo"):
            delay = detail.get("retryDelay")
            if isinstance(delay, str) and re.fullmatch(r"\d+(?:\.\d+)?s", delay):
                return float(delay[:-1])
            if isinstance(delay, dict):
                try:
                    return float(delay.get("seconds", 0)) + float(delay.get("nanos", 0)) / 1e9
                except (TypeError, ValueError):
                    return None
    return None


def _permanent_quota(error: Exception) -> bool:
    for detail in _error_details(error):
        violations = detail.get("violations", [])
        if not isinstance(violations, list):
            continue
        for violation in violations:
            if not isinstance(violation, dict):
                continue
            quota_id = str(violation.get("quotaId", "")).casefold()
            quota_value = str(violation.get("quotaValue", ""))
            if "perday" in quota_id or "per_day" in quota_id or quota_value == "0":
                return True
    return False


class GeminiClient:
    """A single generation round, including metadata and full-budget checks.

    SDK transport retries are disabled so our shared one-retry budget cannot be
    multiplied by hidden retries. A timed-out request is not retried automatically:
    the provider may already have processed it, so the user chooses a manual retry.
    """

    def __init__(
        self, key: str, model: str, *, sdk_client: Any = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        retry_budget: int = MAX_API_RETRIES,
    ) -> None:
        if not key or not key.strip():
            raise GenerationError(
                "configuration", "Set GEMINI_API_KEY in the local .env file before generation."
            )
        if not model or not model.strip():
            raise GenerationError(
                "configuration", "Set an account-accessible GEMINI_MODEL in the local .env file."
            )
        self.model = model.strip()
        self._sleep = sleep_fn
        self._retry_budget = max(0, min(retry_budget, MAX_API_RETRIES))
        self._owns_client = sdk_client is None
        if sdk_client is not None:
            self._client = sdk_client
        else:
            from google import genai
            from google.genai import types

            self._client = genai.Client(
                api_key=key,
                http_options=types.HttpOptions(
                    timeout=API_TIMEOUT_SECONDS * 1000,
                    retry_options=types.HttpRetryOptions(attempts=1),
                ),
            )
        self.last_metadata: dict[str, str | int] = {}
        self._retries_remaining = 0

    def _call(self, operation: Callable[[], Any]) -> Any:
        while True:
            try:
                return operation()
            except GenerationError:
                raise
            except Exception as error:
                name = type(error).__name__.casefold()
                if isinstance(error, TimeoutError) or "timeout" in name:
                    raise GenerationError(
                        "timeout", "The Gemini request timed out. Your work is intact; retry manually.",
                        retryable=True,
                    ) from None
                code = _error_code(error)
                if code in {401, 403}:
                    raise GenerationError(
                        "authentication", "Gemini rejected access. Check the API key and model permissions."
                    ) from None
                if code == 404:
                    raise GenerationError(
                        "model", "The configured Gemini model is unavailable to this account. Check GEMINI_MODEL."
                    ) from None
                if code == 400:
                    reasons = {str(detail.get("reason", "")) for detail in _error_details(error)}
                    if reasons & {"API_KEY_INVALID", "API_KEY_EXPIRED", "API_KEY_NOT_FOUND", "CREDENTIALS_MISSING"}:
                        raise GenerationError(
                            "authentication", "Gemini rejected the API key. Check GEMINI_API_KEY and account access."
                        ) from None
                    raise GenerationError(
                        "request", "Gemini rejected the request or output schema. Check model compatibility and settings."
                    ) from None
                delay = _retry_delay(error)
                temporary = code in {500, 502, 503, 504}
                if code == 429:
                    temporary = delay is not None and not _permanent_quota(error)
                # A long provider delay is respected by leaving a manual retry path.
                if temporary and self._retries_remaining and (delay is None or delay <= 30):
                    self._retries_remaining -= 1
                    self._sleep(delay if delay is not None else 1.0)
                    continue
                if code == 429:
                    message = "Gemini quota or rate limit reached. Check account limits before retrying."
                    if delay is not None and temporary:
                        message = f"Gemini rate limit reached. Wait at least {delay:.0f} seconds before retrying."
                    raise GenerationError("quota", message, retryable=temporary) from None
                if temporary and delay is not None:
                    raise GenerationError(
                        "provider", f"Gemini is temporarily unavailable. Wait at least {delay:.0f} "
                        "seconds before retrying; your work is intact.", retryable=True,
                    ) from None
                raise GenerationError(
                    "provider", "Gemini could not complete the request. Your work is intact; check the connection and retry.",
                    retryable=temporary or code is None,
                ) from None

    def generate(self, prompt: str, capacity: int) -> GenerationResult:
        if isinstance(capacity, bool) or not 1 <= capacity <= MAX_BATCH_TOPICS:
            raise GenerationError("request", "Generation capacity must be between one and ten.")
        self._retries_remaining = min(self._retry_budget, 1)
        try:
            return self._generate(prompt, capacity)
        finally:
            if self._owns_client:
                try:
                    self._client.close()
                except Exception:
                    # Cleanup must not hide the useful, sanitized request result.
                    pass

    def _generate(self, prompt: str, capacity: int) -> GenerationResult:
        from google.genai import types

        metadata = self._call(lambda: self._client.models.get(model=self.model))
        input_limit = getattr(metadata, "input_token_limit", None)
        output_limit = getattr(metadata, "output_token_limit", None)
        actions = getattr(metadata, "supported_actions", None) or []
        if actions and not any("generatecontent" in str(action).casefold() for action in actions):
            raise GenerationError("model", "The configured model does not support content generation.")
        if not isinstance(input_limit, int) or not isinstance(output_limit, int):
            raise GenerationError("model", "Gemini did not provide token limits for this model; generation was blocked.")
        response_allowance = max(4096, capacity * 1400 + 1024)
        if output_limit < response_allowance:
            raise GenerationError(
                "context", "This model has insufficient response capacity. Request a smaller batch or configure a suitable model."
            )
        schema_text = json.dumps(gemini_schema(), ensure_ascii=False)
        # Counting schema text as well as the actual prompt is conservative: schema
        # processing also consumes provider budget and should never be forgotten.
        count = self._call(lambda: self._client.models.count_tokens(
            model=self.model, contents=prompt + "\n\nOutput schema:\n" + schema_text,
        ))
        total_tokens = getattr(count, "total_tokens", None)
        if not isinstance(total_tokens, int) or total_tokens < 1:
            raise GenerationError("context", "Gemini could not confirm the complete request token budget.")
        if total_tokens + response_allowance > input_limit:
            raise GenerationError(
                "context", "The full prompt, remembered angles and response allowance exceed this model's token budget. "
                "Nothing was truncated. Save this workspace and prepare a smaller separate workspace."
            )
        self.last_metadata = {
            "model": str(getattr(metadata, "name", None) or self.model),
            "input_token_limit": input_limit,
            "output_token_limit": output_limit,
            "request_tokens": total_tokens,
            "response_allowance": response_allowance,
        }
        config = types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
            # The Gemini wire subset omits unsupported Pydantic JSON annotations.
            # Full Pydantic and source/evidence checks still run on every response.
            response_schema=gemini_schema(),
            max_output_tokens=response_allowance,
        )
        response = self._call(lambda: self._client.models.generate_content(
            model=self.model, contents=prompt, config=config,
        ))
        candidates = getattr(response, "candidates", None) or []
        for candidate in candidates:
            finish = str(getattr(candidate, "finish_reason", "") or "").upper()
            if "MAX_TOKENS" in finish:
                raise GenerationError(
                    "invalid_output", "Gemini stopped before completing its response. Try a smaller batch.",
                    retryable=True,
                )
            if any(reason in finish for reason in ("SAFETY", "RECITATION", "BLOCKLIST", "PROHIBITED")):
                raise GenerationError(
                    "blocked", "Gemini did not return usable content because the request was blocked. Review the sources or brief."
                )
        try:
            parsed = getattr(response, "parsed", None)
            if parsed is not None:
                return GenerationResult.model_validate(parsed)
            text = getattr(response, "text", None)
            if not text:
                # Empty body can occur when the provider is under load. One retry is
                # allowed if the shared budget has not already been spent on a network
                # error above. A second empty response hands off to the fallback chain.
                if self._retries_remaining:
                    self._retries_remaining -= 1
                    self._sleep(1.0)
                    return self._generate(prompt, capacity)
                raise GenerationError(
                    "invalid_output", "Gemini returned no structured response. You can retry.", retryable=True
                )
            return GenerationResult.model_validate_json(text)
        except (ValidationError, ValueError, TypeError):
            raise GenerationError(
                "invalid_output", "Gemini returned incomplete or invalid structured data. You can retry.",
                retryable=True,
            ) from None
