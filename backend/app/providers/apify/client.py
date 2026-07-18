from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Mapping

from apify_client import ApifyClient

from .costs import CostEstimate
from .errors import (
    ApifyAuthenticationError,
    ApifyProviderError,
    ApifyRateLimitError,
    ApifyRequestError,
    ApifyRunFailedError,
    ApifySchemaError,
    ApifyTimeoutError,
    ErrorContext,
    redact_text,
)
from .inputs import ActorRequest


@dataclass(frozen=True)
class ApifyRunOutcome:
    actor_id: str
    run_id: str
    dataset_id: str
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    build_id: str | None
    build_number: str | None
    cost_usd: float | None
    items: list[object]


def _read(value: object, *names: str) -> Any:
    """Read current typed-client attributes and legacy mapping keys safely."""

    for name in names:
        if isinstance(value, Mapping) and name in value:
            return value[name]
        if hasattr(value, name):
            return getattr(value, name)
    return None


def _datetime(value: object) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


class ApifyClientAdapter:
    """Small testable facade over Apify's maintained synchronous Python client."""

    def __init__(
        self,
        *,
        token: str,
        api_base: str = "https://api.apify.com",
        request_timeout_seconds: int = 60,
        run_timeout_seconds: int = 600,
        max_retries: int = 3,
        client: Any | None = None,
    ) -> None:
        self._token = token
        self.run_timeout_seconds = run_timeout_seconds
        self._client = client or ApifyClient(
            token=token,
            api_url=api_base.rstrip("/").removesuffix("/v2"),
            max_retries=max_retries,
            timeout_short=timedelta(seconds=request_timeout_seconds),
            timeout_medium=timedelta(seconds=request_timeout_seconds),
            timeout_long=timedelta(seconds=max(request_timeout_seconds, run_timeout_seconds)),
            timeout_max=timedelta(seconds=max(request_timeout_seconds, run_timeout_seconds)),
        )

    def run_actor(self, request: ActorRequest, estimate: CostEstimate) -> ApifyRunOutcome:
        try:
            run = self._client.actor(request.actor_id).call(
                run_input=request.payload,
                max_items=request.maximum_result_count,
                max_total_charge_usd=Decimal(str(estimate.enforced_max_charge_usd)),
                restart_on_error=False,
                run_timeout=timedelta(seconds=self.run_timeout_seconds),
                wait_duration=timedelta(seconds=self.run_timeout_seconds),
                logger=None,
            )
        except Exception as error:
            raise self._translate(error, category="actor_call") from None
        if run is None:
            raise ApifyTimeoutError(
                "Apify Actor did not finish within the configured timeout",
                context=ErrorContext(category="actor_run_timeout"),
            )

        status = str(_read(run, "status") or "UNKNOWN").upper()
        run_id = str(_read(run, "id") or "")
        dataset_id = str(_read(run, "default_dataset_id", "defaultDatasetId") or "")
        if not run_id:
            raise ApifySchemaError(
                "Apify Actor run did not include a run ID",
                context=ErrorContext(category="missing_run_id"),
            )
        if not dataset_id:
            raise ApifySchemaError(
                "Apify Actor run did not include a default dataset ID",
                context=ErrorContext(category="missing_dataset_id", run_id=run_id),
            )

        items = self.get_dataset_items(
            dataset_id, maximum_items=request.maximum_result_count
        )
        if status != "SUCCEEDED" and not items:
            message = _read(run, "status_message", "statusMessage") or status
            raise ApifyRunFailedError(
                f"Apify Actor run ended with {status}: {redact_text(message, [self._token])}",
                context=ErrorContext(category="actor_run_failed", run_id=run_id),
            )

        usage_total = _read(run, "usage_total_usd", "usageTotalUsd")
        return ApifyRunOutcome(
            actor_id=request.actor_id,
            run_id=run_id,
            dataset_id=dataset_id,
            status=status,
            started_at=_datetime(_read(run, "started_at", "startedAt")),
            finished_at=_datetime(_read(run, "finished_at", "finishedAt")),
            build_id=_read(run, "build_id", "buildId"),
            build_number=_read(run, "build_number", "buildNumber"),
            cost_usd=float(usage_total) if usage_total is not None else None,
            items=items,
        )

    def get_dataset_items(self, dataset_id: str, *, maximum_items: int) -> list[object]:
        try:
            iterator = self._client.dataset(dataset_id).iterate_items(
                limit=maximum_items,
                clean=True,
            )
            return list(iterator)[:maximum_items]
        except Exception as error:
            raise self._translate(error, category="dataset_items") from None

    def health_check(self) -> dict[str, object]:
        try:
            user = self._client.user().get()
        except Exception as error:
            raise self._translate(error, category="health_check") from None
        return {
            "ok": user is not None,
            "provider": "apify",
            "network_check": "completed",
        }

    def _translate(self, error: Exception, *, category: str) -> ApifyProviderError:
        if isinstance(error, ApifyProviderError):
            return error
        status_code = getattr(error, "status_code", None)
        name = type(error).__name__.lower()
        message = redact_text(error, [self._token])
        context = ErrorContext(category=category, status_code=status_code)
        if status_code in {401, 403} or "authentication" in name:
            return ApifyAuthenticationError(message, context=context)
        if status_code == 429 or "ratelimit" in name or "rate_limit" in name:
            return ApifyRateLimitError(message, context=context)
        if "timeout" in name or "timed out" in message.lower():
            return ApifyTimeoutError(message, context=context)
        return ApifyRequestError(message, context=context)
