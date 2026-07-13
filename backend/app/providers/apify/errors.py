from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


REDACTED = "[REDACTED]"


def redact_text(value: object, secrets: Iterable[str] = ()) -> str:
    """Return a log-safe message without provider credentials."""

    text = str(value)
    for secret in secrets:
        if secret:
            text = text.replace(secret, REDACTED)
    return text


@dataclass(frozen=True)
class ErrorContext:
    category: str
    status_code: int | None = None
    retryable: bool = False
    run_id: str | None = None


class ApifyProviderError(RuntimeError):
    def __init__(self, message: str, *, context: ErrorContext) -> None:
        super().__init__(message)
        self.context = context


class ApifyConfigurationError(ApifyProviderError):
    pass


class ApifyAuthenticationError(ApifyProviderError):
    pass


class ApifyRateLimitError(ApifyProviderError):
    pass


class ApifyRequestError(ApifyProviderError):
    pass


class ApifyTimeoutError(ApifyProviderError):
    pass


class ApifySchemaError(ApifyProviderError):
    pass


class ApifyRunFailedError(ApifyProviderError):
    pass


class ApifyBudgetError(ApifyProviderError):
    pass
