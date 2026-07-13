from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import quote

import httpx
from pydantic import ValidationError

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
from .schemas import ActorRun, ActorRunEnvelope


TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"}
TRANSIENT_STATUSES = {"READY", "RUNNING", "TIMING-OUT", "ABORTING"}
QueryValue = str | int | float | bool


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


class ApifyAsyncClient:
    """Minimal async Apify v2 client with safe retry semantics.

    Actor-start POST requests are never retried automatically because a timeout can
    be ambiguous and a retry could start a second paid run. Idempotent GET requests
    retry rate limits, transient server responses and transport failures.
    """

    def __init__(
        self,
        *,
        token: str,
        api_base: str = "https://api.apify.com/v2",
        request_timeout_seconds: int = 60,
        run_timeout_seconds: int = 900,
        poll_interval_seconds: float = 2,
        max_idempotent_attempts: int = 4,
        dataset_page_size: int = 1000,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._token = token
        self.api_base = api_base.rstrip("/")
        self.request_timeout_seconds = request_timeout_seconds
        self.run_timeout_seconds = run_timeout_seconds
        self.poll_interval_seconds = max(0, poll_interval_seconds)
        self.max_idempotent_attempts = max(1, max_idempotent_attempts)
        self.dataset_page_size = max(1, min(dataset_page_size, 1000))
        self._transport = transport

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.api_base,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/json",
                "User-Agent": "SignalScope/0.1 ApifyProvider",
            },
            timeout=self.request_timeout_seconds,
            transport=self._transport,
        )

    async def start_run(
        self, request: ActorRequest, estimate: CostEstimate
    ) -> ActorRun:
        actor_id = quote(request.actor_id, safe="~")
        value = await self._request_json(
            "POST",
            f"/actors/{actor_id}/runs",
            params={
                "timeout": self.run_timeout_seconds,
                "maxItems": request.maximum_result_count,
                "maxTotalChargeUsd": estimate.enforced_max_charge_usd,
                "restartOnError": "false",
                "waitForFinish": 0,
            },
            json=request.payload,
            idempotent=False,
        )
        return self._parse_run(value)

    async def wait_for_run(
        self, initial: ActorRun, *, allow_partial_dataset: bool = False
    ) -> ActorRun:
        run = initial
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self.run_timeout_seconds
        while run.status.upper() not in TERMINAL_STATUSES:
            if run.status.upper() not in TRANSIENT_STATUSES:
                raise ApifySchemaError(
                    f"Apify returned unknown run status: {redact_text(run.status, [self._token])}",
                    context=ErrorContext(category="unknown_run_status", run_id=run.id),
                )
            if loop.time() >= deadline:
                raise ApifyTimeoutError(
                    "Timed out while waiting for the Apify Actor run to finish",
                    context=ErrorContext(
                        category="run_poll_timeout", retryable=False, run_id=run.id
                    ),
                )
            if self.poll_interval_seconds:
                await asyncio.sleep(self.poll_interval_seconds)
            value = await self._request_json(
                "GET", f"/actor-runs/{quote(run.id)}", idempotent=True
            )
            run = self._parse_run(value)
        if run.status.upper() != "SUCCEEDED" and not allow_partial_dataset:
            summary = redact_text(run.status_message or run.status, [self._token])
            raise ApifyRunFailedError(
                f"Apify Actor run ended with {run.status}: {summary}",
                context=ErrorContext(category="actor_run_failed", run_id=run.id),
            )
        return run

    async def get_dataset_items(self, dataset_id: str, *, maximum_items: int) -> list[object]:
        items: list[object] = []
        offset = 0
        while len(items) < maximum_items:
            limit = min(self.dataset_page_size, maximum_items - len(items))
            page = await self._request_json(
                "GET",
                f"/datasets/{quote(dataset_id)}/items",
                params={"offset": offset, "limit": limit, "clean": 1, "format": "json"},
                idempotent=True,
            )
            if not isinstance(page, list):
                raise ApifySchemaError(
                    "Apify dataset items response must be a JSON array",
                    context=ErrorContext(category="dataset_schema"),
                )
            items.extend(page[:limit])
            if len(page) < limit:
                break
            offset += len(page)
        return items[:maximum_items]

    async def run_actor(
        self, request: ActorRequest, estimate: CostEstimate
    ) -> ApifyRunOutcome:
        started = await self.start_run(request, estimate)
        completed = await self.wait_for_run(started, allow_partial_dataset=True)
        if not completed.dataset_id:
            if completed.status.upper() != "SUCCEEDED":
                summary = redact_text(
                    completed.status_message or completed.status, [self._token]
                )
                raise ApifyRunFailedError(
                    f"Apify Actor run ended with {completed.status}: {summary}",
                    context=ErrorContext(
                        category="actor_run_failed", run_id=completed.id
                    ),
                )
            raise ApifySchemaError(
                "Successful Apify Actor run did not include a default dataset ID",
                context=ErrorContext(category="missing_dataset_id", run_id=completed.id),
            )
        items = await self.get_dataset_items(
            completed.dataset_id, maximum_items=request.maximum_result_count
        )
        if completed.status.upper() != "SUCCEEDED" and not items:
            summary = redact_text(completed.status_message or completed.status, [self._token])
            raise ApifyRunFailedError(
                f"Apify Actor run ended with {completed.status}: {summary}",
                context=ErrorContext(
                    category="actor_run_failed", run_id=completed.id
                ),
            )
        return ApifyRunOutcome(
            actor_id=request.actor_id,
            run_id=completed.id,
            dataset_id=completed.dataset_id,
            status=completed.status,
            started_at=completed.started_at,
            finished_at=completed.finished_at,
            build_id=completed.build_id,
            build_number=completed.build_number,
            cost_usd=completed.usage_total_usd,
            items=items,
        )

    async def health_check(self) -> dict[str, object]:
        value = await self._request_json("GET", "/users/me", idempotent=True)
        return {
            "ok": isinstance(value, dict) and isinstance(value.get("data"), dict),
            "provider": "apify",
            "network_check": "completed",
        }

    def _parse_run(self, value: object) -> ActorRun:
        try:
            return ActorRunEnvelope.model_validate(value).data
        except ValidationError as error:
            raise ApifySchemaError(
                redact_text(error, [self._token]),
                context=ErrorContext(category="run_schema"),
            ) from None

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, QueryValue] | None = None,
        json: dict[str, Any] | None = None,
        idempotent: bool,
    ) -> Any:
        attempts = self.max_idempotent_attempts if idempotent else 1
        last_error: ApifyProviderError | None = None
        for attempt in range(attempts):
            try:
                async with self._client() as client:
                    response = await client.request(method, path, params=params, json=json)
            except httpx.TimeoutException:
                category = "request_timeout" if idempotent else "ambiguous_actor_start_timeout"
                last_error = ApifyTimeoutError(
                    "Apify request timed out",
                    context=ErrorContext(
                        category=category, retryable=idempotent and attempt + 1 < attempts
                    ),
                )
                if idempotent and attempt + 1 < attempts:
                    await asyncio.sleep(self._backoff(attempt))
                    continue
                raise last_error from None
            except httpx.TransportError:
                last_error = ApifyRequestError(
                    "Apify transport request failed",
                    context=ErrorContext(
                        category="transport_error",
                        retryable=idempotent and attempt + 1 < attempts,
                    ),
                )
                if idempotent and attempt + 1 < attempts:
                    await asyncio.sleep(self._backoff(attempt))
                    continue
                raise last_error from None

            if 200 <= response.status_code < 300:
                try:
                    return response.json()
                except ValueError:
                    raise ApifySchemaError(
                        "Apify returned a non-JSON response",
                        context=ErrorContext(
                            category="invalid_json", status_code=response.status_code
                        ),
                    ) from None

            summary = self._response_error(response)
            if response.status_code in {401, 403}:
                raise ApifyAuthenticationError(
                    summary,
                    context=ErrorContext(
                        category="authentication", status_code=response.status_code
                    ),
                )
            if response.status_code == 429:
                retryable = idempotent and attempt + 1 < attempts
                last_error = ApifyRateLimitError(
                    summary,
                    context=ErrorContext(
                        category="rate_limit",
                        status_code=response.status_code,
                        retryable=retryable,
                    ),
                )
                if retryable:
                    await asyncio.sleep(self._retry_after(response, attempt))
                    continue
                raise last_error
            if response.status_code >= 500:
                retryable = idempotent and attempt + 1 < attempts
                last_error = ApifyRequestError(
                    summary,
                    context=ErrorContext(
                        category="provider_server_error",
                        status_code=response.status_code,
                        retryable=retryable,
                    ),
                )
                if retryable:
                    await asyncio.sleep(self._backoff(attempt))
                    continue
                raise last_error
            raise ApifyRequestError(
                summary,
                context=ErrorContext(
                    category="provider_request_error", status_code=response.status_code
                ),
            )
        if last_error is not None:
            raise last_error
        raise AssertionError("Apify request attempts exhausted without a result")

    def _response_error(self, response: httpx.Response) -> str:
        summary = f"Apify request failed with HTTP {response.status_code}"
        try:
            value = response.json()
            if isinstance(value, dict):
                error = value.get("error")
                if isinstance(error, dict):
                    detail = error.get("message") or error.get("type")
                    if detail:
                        summary = f"{summary}: {detail}"
        except ValueError:
            pass
        return redact_text(summary, [self._token])

    @staticmethod
    def _backoff(attempt: int) -> float:
        return min(8.0, float(2**attempt))

    def _retry_after(self, response: httpx.Response, attempt: int) -> float:
        value = response.headers.get("Retry-After")
        if value:
            try:
                return max(0.0, float(value))
            except ValueError:
                try:
                    retry_at = parsedate_to_datetime(value)
                    if retry_at.tzinfo is None:
                        retry_at = retry_at.replace(tzinfo=timezone.utc)
                    return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())
                except (TypeError, ValueError, OverflowError):
                    pass
        return self._backoff(attempt)
