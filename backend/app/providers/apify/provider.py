from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Iterable

from pydantic import SecretStr

from app.providers.base import ProviderVideo

from .capabilities import provider_capabilities
from .client import ApifyClientAdapter
from .costs import CostEstimate, estimate_cost
from .errors import (
    ApifyConfigurationError,
    ApifyRateLimitError,
    ApifyRequestError,
    ApifyRunFailedError,
    ApifySchemaError,
    ApifyTimeoutError,
    ErrorContext,
)
from .inputs import (
    ActorContract,
    ActorRequest,
    CollectionType,
    SearchDateRange,
    build_direct_refresh_request,
    build_discover_request,
    build_hashtag_request,
    build_keyword_request,
    build_profile_request,
    safety_assertions,
)
from .normalizer import normalize_items
from .settings import ApifyProviderSettings


API_DOJO_ACTOR_ID = "apidojo/tiktok-scraper-api"
CLOCKWORKS_ACTOR_ID = "clockworks/tiktok-scraper"
PRIMARY_ACTOR_ID = API_DOJO_ACTOR_ID
FALLBACK_ACTOR_ID = CLOCKWORKS_ACTOR_ID
DISCOVER_ACTOR_ID = "clockworks/tiktok-discover-scraper"
# Compatibility exports for integrations written against the first connector.
DISCOVERY_ACTOR_ID = PRIMARY_ACTOR_ID
PROFILE_ACTOR_ID = PRIMARY_ACTOR_ID
ACTOR_ID = PRIMARY_ACTOR_ID
PROVIDER_NAME = f"apify:{PRIMARY_ACTOR_ID}"

FALLBACK_ERRORS = (
    ApifyRateLimitError,
    ApifyRequestError,
    ApifyRunFailedError,
    ApifySchemaError,
    ApifyTimeoutError,
)


class ApifyTikTokProvider:
    """Provider-protocol adapter backed by typed, separately testable Apify components."""

    def __init__(
        self,
        *,
        token: str = "",
        enabled: bool = False,
        provider_mode: str = "live",
        actor_id: str = PRIMARY_ACTOR_ID,
        fallback_actor_id: str = FALLBACK_ACTOR_ID,
        enable_fallback: bool = True,
        fallback_max_total_charge_usd: float = 0.5,
        discover_actor_id: str = DISCOVER_ACTOR_ID,
        enable_discover: bool = False,
        base_url: str = "https://api.apify.com",
        search_queries: Iterable[str] = (),
        hashtags: Iterable[str] = (),
        profiles: Iterable[str] = (),
        post_urls: Iterable[str] = (),
        results_per_page: int = 25,
        max_results_per_query: int | None = None,
        max_items: int | None = None,
        max_total_charge_usd: float | None = None,
        timeout_seconds: int | None = None,
        run_timeout_seconds: int = 600,
        request_timeout_seconds: int = 60,
        max_retries: int = 3,
        default_language: str = "en",
        proxy_country_code: str | None = None,
        default_market: str = "GB",
        supported_markets: Iterable[str] = ("GB", "PL"),
        monthly_budget_usd: float = 50,
        monthly_spend_usd: float = 0,
        toy_discovery_enabled: bool = True,
        toy_monitoring_percentage: int = 10,
        raw_payload_retention_days: int = 14,
        client: Any | None = None,
        settings: ApifyProviderSettings | None = None,
    ) -> None:
        selected_market = (
            proxy_country_code
            if proxy_country_code and proxy_country_code.lower() != "none"
            else default_market
        )
        if settings is None:
            api_base = base_url.rstrip("/")
            selected_timeout = timeout_seconds or run_timeout_seconds
            self.settings = ApifyProviderSettings(
                enabled=enabled,
                token=SecretStr(token),
                api_base=api_base,
                primary_actor_id=actor_id,
                fallback_actor_id=fallback_actor_id,
                enable_fallback=enable_fallback,
                fallback_max_total_charge_usd=fallback_max_total_charge_usd,
                discover_actor_id=discover_actor_id,
                enable_discover=enable_discover,
                max_results_per_query=max_results_per_query or results_per_page,
                max_items_per_run=max_items or 500,
                max_total_charge_usd=max_total_charge_usd or 5,
                max_retries=max_retries,
                default_market=selected_market,
                default_language=default_language,
                supported_markets=tuple(supported_markets),
                run_timeout_seconds=selected_timeout,
                request_timeout_seconds=request_timeout_seconds,
                monthly_budget_usd=monthly_budget_usd,
                raw_payload_retention_days=raw_payload_retention_days,
                toy_discovery_enabled=toy_discovery_enabled,
                toy_monitoring_percentage=toy_monitoring_percentage,
                provider_mode=provider_mode,
            )
        else:
            self.settings = settings
        self.search_queries = self._clean(search_queries)
        self.hashtags = self._clean(hashtags, prefix="#")
        self.profiles = self._clean(profiles, prefix="@")
        self.post_urls = self._clean(post_urls)
        self.max_items = max_items or self.settings.max_items_per_run
        self.explicit_run_cap_usd = (
            max_total_charge_usd or self.settings.max_total_charge_usd
        )
        self.explicit_fallback_cap_usd = self.settings.fallback_max_total_charge_usd
        self.monthly_spend_usd = max(0, monthly_spend_usd)
        self._videos: dict[str, ProviderVideo] = {}
        self.last_run_quality: dict[str, Any] = {}
        self._client = ApifyClientAdapter(
            token=self.settings.token.get_secret_value(),
            api_base=self.settings.api_base,
            request_timeout_seconds=self.settings.request_timeout_seconds,
            run_timeout_seconds=self.settings.run_timeout_seconds,
            max_retries=self.settings.max_retries,
            client=client,
        )

    @staticmethod
    def _clean(values: Iterable[str], *, prefix: str = "") -> list[str]:
        return list(
            dict.fromkeys(value.strip().removeprefix(prefix) for value in values if value.strip())
        )

    @property
    def actor_id(self) -> str:
        return self.settings.primary_actor_id

    @staticmethod
    def _contract_for_actor(actor_id: str) -> ActorContract:
        if actor_id == API_DOJO_ACTOR_ID:
            return ActorContract.API_DOJO
        if actor_id == CLOCKWORKS_ACTOR_ID:
            return ActorContract.CLOCKWORKS
        raise ApifyConfigurationError(
            f"Unsupported Actor contract: {actor_id}",
            context=ErrorContext(category="unsupported_actor_contract"),
        )

    @property
    def enabled(self) -> bool:
        return self.settings.live_enabled

    def keyword_request(
        self,
        keywords: Iterable[str],
        *,
        market: str | None = None,
        result_limit: int | None = None,
        date_range: SearchDateRange = SearchDateRange.PAST_WEEK,
    ) -> ActorRequest:
        return build_keyword_request(
            actor_id=self.settings.primary_actor_id,
            keywords=keywords,
            market=market or self.settings.default_market,
            supported_markets=self.settings.supported_markets,
            result_limit=result_limit or self.settings.max_results_per_query,
            maximum_per_query=self.settings.max_results_per_query,
            date_range=date_range,
            language=self.settings.default_language,
            contract=self._contract_for_actor(self.settings.primary_actor_id),
        )

    def hashtag_request(
        self,
        hashtags: Iterable[str],
        *,
        market: str | None = None,
        result_limit: int | None = None,
    ) -> ActorRequest:
        return build_hashtag_request(
            actor_id=self.settings.primary_actor_id,
            hashtags=hashtags,
            market=market or self.settings.default_market,
            supported_markets=self.settings.supported_markets,
            result_limit=result_limit or self.settings.max_results_per_query,
            maximum_per_query=self.settings.max_results_per_query,
            language=self.settings.default_language,
            contract=self._contract_for_actor(self.settings.primary_actor_id),
        )

    def profile_request(
        self,
        profiles: Iterable[str],
        *,
        market: str | None = None,
        result_limit: int | None = None,
        use_enrichment_actor: bool = False,
    ) -> ActorRequest:
        if use_enrichment_actor:
            raise ApifyConfigurationError(
                "A separate profile Actor is not configured; use the primary TikTok Actor",
                context=ErrorContext(category="unsupported_profile_actor"),
            )
        return build_profile_request(
            actor_id=self.settings.primary_actor_id,
            profiles=profiles,
            market=market or self.settings.default_market,
            supported_markets=self.settings.supported_markets,
            result_limit=result_limit or self.settings.max_results_per_query,
            maximum_per_query=self.settings.max_results_per_query,
            enrichment=False,
            language=self.settings.default_language,
            contract=self._contract_for_actor(self.settings.primary_actor_id),
        )

    def direct_refresh_request(
        self,
        video_urls: Iterable[str],
        *,
        market: str | None = None,
    ) -> ActorRequest:
        return build_direct_refresh_request(
            actor_id=self.settings.primary_actor_id,
            video_urls=video_urls,
            market=market or self.settings.default_market,
            supported_markets=self.settings.supported_markets,
            maximum_urls=self.settings.max_results_per_query,
            language=self.settings.default_language,
            contract=self._contract_for_actor(self.settings.primary_actor_id),
        )

    def discover_expansion_request(
        self,
        hashtags: Iterable[str],
        *,
        market: str | None = None,
        result_limit: int | None = None,
    ) -> ActorRequest:
        if not self.settings.enable_discover:
            raise ApifyConfigurationError(
                "APIFY_ENABLE_DISCOVER is false",
                context=ErrorContext(category="discover_actor_disabled"),
            )
        return build_discover_request(
            actor_id=self.settings.discover_actor_id,
            hashtags=hashtags,
            market=market or self.settings.default_market,
            supported_markets=self.settings.supported_markets,
            result_limit=result_limit or self.settings.max_results_per_query,
            maximum_per_query=self.settings.max_results_per_query,
            language=self.settings.default_language,
        )

    def preflight(self, request: ActorRequest) -> dict[str, object]:
        effective = self._effective_request(request)
        estimate = self._estimate(effective)
        safety = safety_assertions(effective)
        return {
            "actor_id": effective.actor_id,
            "collection_type": effective.collection_type.value,
            "market": effective.market,
            "language": effective.language,
            "actor_payload": effective.payload,
            "maximum_result_count": effective.maximum_result_count,
            "cost": estimate.as_dict(),
            "safety": safety,
            "safe_to_execute": all(safety.values()),
            "token_transport": "Backend Authorization header only",
            "token_in_payload": False,
            "token_in_url": False,
            "token_logging": "Redacted",
            "fallback": {
                "enabled": self._fallback_allowed(effective),
                "actor_id": self.settings.fallback_actor_id,
                "max_total_charge_usd": self.explicit_fallback_cap_usd,
                "trigger": "primary provider run, request, timeout, rate-limit, or schema failure",
            },
            "maximum_combined_charge_usd": round(
                estimate.enforced_max_charge_usd
                + (self.explicit_fallback_cap_usd if self._fallback_allowed(effective) else 0),
                4,
            ),
        }

    async def collect(self, request: ActorRequest) -> list[ProviderVideo]:
        try:
            return await self._collect_once(request)
        except FALLBACK_ERRORS as primary_error:
            if not self._fallback_allowed(request):
                raise
            fallback_request = self._fallback_request(request)
            failure_category = primary_error.context.category
            try:
                videos = await self._collect_once(fallback_request, fallback=True)
            except FALLBACK_ERRORS as fallback_error:
                self.last_run_quality = {
                    "status": "failed",
                    "primary_actor_id": request.actor_id,
                    "fallback_actor_id": fallback_request.actor_id,
                    "fallback_used": True,
                    "primary_failure_category": failure_category,
                    "fallback_failure_category": fallback_error.context.category,
                }
                raise
            self.last_run_quality.update(
                {
                    "fallback_used": True,
                    "primary_actor_id": request.actor_id,
                    "fallback_actor_id": fallback_request.actor_id,
                    "primary_failure_category": failure_category,
                }
            )
            return videos

    async def _collect_once(
        self, request: ActorRequest, *, fallback: bool = False
    ) -> list[ProviderVideo]:
        require_discovery = request.collection_type in {
            CollectionType.KEYWORD,
            CollectionType.HASHTAG,
            CollectionType.PROFILE,
        }
        issues = self.settings.configuration_issues(require_discovery=require_discovery)
        if issues:
            raise ApifyConfigurationError(
                "; ".join(issues), context=ErrorContext(category="provider_disabled")
            )
        effective = self._effective_request(request)
        safety = safety_assertions(effective)
        if not all(safety.values()):
            raise ApifyConfigurationError(
                "Actor input failed mandatory collection-safety assertions",
                context=ErrorContext(category="unsafe_actor_input"),
            )
        outcome = await asyncio.to_thread(
            self._client.run_actor,
            effective,
            self._estimate(effective, fallback=fallback),
        )
        if outcome.items and all(
            isinstance(item, dict) and item.get("demo") is True
            for item in outcome.items
        ):
            raise ApifyRunFailedError(
                "The Actor returned demo-only records because API access is unavailable "
                "on the current Apify plan",
                context=ErrorContext(
                    category="provider_demo_mode",
                    run_id=outcome.run_id,
                ),
            )
        retrieved_at = datetime.now(timezone.utc).replace(tzinfo=None)
        normalized = normalize_items(
            outcome.items,
            request=effective,
            run_id=outcome.run_id,
            dataset_id=outcome.dataset_id,
            retrieved_at=retrieved_at,
            secrets=[self.settings.token.get_secret_value()],
        )
        if not normalized.videos and normalized.quarantined:
            raise ApifySchemaError(
                "Apify returned no usable TikTok video items",
                context=ErrorContext(
                    category="no_usable_items", run_id=outcome.run_id
                ),
            )
        unique_videos: dict[str, ProviderVideo] = {}
        duplicate_records = 0
        for video in normalized.videos:
            in_run = unique_videos.get(video.id)
            if in_run:
                duplicate_records += 1
                video.discovery_queries = list(
                    dict.fromkeys([*in_run.discovery_queries, *video.discovery_queries])
                )
            unique_videos[video.id] = video
        for video in unique_videos.values():
            previous = self._videos.get(video.id)
            if previous:
                video.discovery_queries = list(
                    dict.fromkeys([*previous.discovery_queries, *video.discovery_queries])
                )
            self._videos[video.id] = video
        if outcome.cost_usd is not None:
            self.monthly_spend_usd = round(self.monthly_spend_usd + outcome.cost_usd, 4)
        metric_names = {"views", "likes", "comments", "shares", "saves"}
        missing_metrics = sum(
            len(metric_names.intersection(video.missing_fields))
            for video in unique_videos.values()
        )
        possible_metrics = len(unique_videos) * len(metric_names)
        related_term_values: set[str] = set()
        for video in unique_videos.values():
            values = video.discovery_context.get("related_terms")
            if isinstance(values, list):
                related_term_values.update(
                    term for term in values if isinstance(term, str)
                )
        related_terms = sorted(related_term_values)
        self.last_run_quality = {
            "provider": f"apify:{effective.actor_id}",
            "actor_id": effective.actor_id,
            "actor_version": outcome.build_number,
            "external_run_id": outcome.run_id,
            "dataset_id": outcome.dataset_id,
            "collection_type": effective.collection_type.value,
            "market": effective.market,
            "language": effective.language,
            "query_provenance": list(effective.source_values),
            "related_discovery_terms": related_terms,
            "associated_creators": sorted(
                {video.username for video in unique_videos.values() if video.username}
            ),
            "associated_sounds": sorted(
                {
                    video.sound_id
                    for video in unique_videos.values()
                    if video.sound_id
                }
            ),
            "status": outcome.status.lower(),
            "partial_dataset": outcome.status.upper() != "SUCCEEDED",
            "started_at": outcome.started_at.isoformat() if outcome.started_at else None,
            "finished_at": outcome.finished_at.isoformat() if outcome.finished_at else None,
            "returned_records": len(outcome.items),
            "accepted_records": len(unique_videos),
            "duplicate_records": duplicate_records,
            "invalid_records": len(normalized.quarantined),
            "missing_field_rate": round(
                missing_metrics / possible_metrics if possible_metrics else 0, 4
            ),
            "quarantine": [
                record.to_quality_record() for record in normalized.quarantined
            ],
            "schema_fingerprints": sorted(normalized.schema_fingerprints),
            "cost_usd": outcome.cost_usd,
            "currency": "USD",
            "payload_retained": False,
            "configured_raw_payload_retention_days": self.settings.raw_payload_retention_days,
            "fallback_used": fallback,
        }
        return list(unique_videos.values())

    def collect_sync(self, request: ActorRequest) -> list[ProviderVideo]:
        return self._run_sync(self.collect(request))

    async def discover_videos_async(self) -> list[ProviderVideo]:
        requests: list[ActorRequest] = []
        if self.search_queries:
            requests.append(self.keyword_request(self.search_queries))
        if self.hashtags:
            requests.append(self.hashtag_request(self.hashtags))
            if self.settings.enable_discover:
                requests.append(self.discover_expansion_request(self.hashtags))
        if self.profiles:
            requests.append(self.profile_request(self.profiles))
        if self.post_urls:
            requests.append(self.direct_refresh_request(self.post_urls))
        if not requests:
            raise ApifyConfigurationError(
                "At least one keyword, hashtag, profile, or canonical video URL is required",
                context=ErrorContext(category="missing_discovery_input"),
            )
        videos: dict[str, ProviderVideo] = {}
        run_summaries: list[dict[str, Any]] = []
        for request in requests:
            for video in await self.collect(request):
                previous = videos.get(video.id)
                if previous:
                    video.discovery_queries = list(
                        dict.fromkeys([*previous.discovery_queries, *video.discovery_queries])
                    )
                videos[video.id] = video
            run_summaries.append(dict(self.last_run_quality))
        self.last_run_quality = {
            "status": (
                "success"
                if all(not bool(run.get("partial_dataset")) for run in run_summaries)
                else "partial"
            ),
            "partial_dataset": any(
                bool(run.get("partial_dataset")) for run in run_summaries
            ),
            "runs": run_summaries,
            "returned_records": sum(int(run["returned_records"]) for run in run_summaries),
            "accepted_records": len(videos),
            "invalid_records": sum(int(run["invalid_records"]) for run in run_summaries),
            "cost_usd": round(
                sum(float(run.get("cost_usd") or 0) for run in run_summaries), 4
            ),
        }
        return list(videos.values())

    def discover_videos(self) -> list[ProviderVideo]:
        return self._run_sync(self.discover_videos_async())

    async def refresh_video_urls_async(self, video_urls: list[str]) -> list[ProviderVideo]:
        return await self.collect(self.direct_refresh_request(video_urls))

    def refresh_video_urls(self, video_urls: list[str]) -> list[ProviderVideo]:
        return self._run_sync(self.refresh_video_urls_async(video_urls))

    def get_video_metrics(self, video_ids: list[str]) -> dict[str, dict[str, int | None]]:
        cached = {
            video_id: self._videos[video_id].metrics
            for video_id in video_ids
            if video_id in self._videos
        }
        unknown = [video_id for video_id in video_ids if video_id not in cached]
        if unknown:
            raise ValueError("Refresh unknown videos by canonical TikTok URL first")
        return cached

    async def get_creator_recent_videos_async(self, creator_id: str) -> list[ProviderVideo]:
        request = self.profile_request([creator_id])
        return await self.collect(request)

    def get_creator_recent_videos(self, creator_id: str) -> list[ProviderVideo]:
        return self._run_sync(self.get_creator_recent_videos_async(creator_id))

    def get_creator_profile(self, creator_id: str) -> dict[str, Any]:
        videos = self.get_creator_recent_videos(creator_id)
        first = videos[0] if videos else None
        return {
            "id": creator_id.removeprefix("@"),
            "username": first.username if first else creator_id.removeprefix("@"),
            "display_name": first.creator_display_name if first else None,
            "profile_url": first.creator_profile_url if first else None,
            "followers": first.creator_followers if first else None,
            "verified": first.creator_verified if first else None,
            "account_region": first.creator_account_region if first else None,
            "provider": first.provider if first else f"apify:{self.settings.primary_actor_id}",
            "recent_video_count": len(videos),
        }

    def discover_hashtags(self) -> list[dict[str, Any]]:
        observed: dict[str, set[str]] = {}
        for video in self._videos.values():
            for hashtag in video.hashtags:
                observed.setdefault(hashtag, set()).add(video.creator_id)
        return [
            {
                "name": name,
                "observed_videos": sum(name in video.hashtags for video in self._videos.values()),
                "unique_creators": len(creators),
                "provider": f"apify:{self.settings.primary_actor_id}",
            }
            for name, creators in observed.items()
        ]

    def discover_sounds(self) -> list[dict[str, Any]]:
        sounds: dict[str, dict[str, Any]] = {}
        for video in self._videos.values():
            if video.sound_id:
                sounds.setdefault(
                    video.sound_id,
                    {
                        "id": video.sound_id,
                        "title": video.sound_title,
                        "author": video.sound_author,
                        "original": video.sound_original,
                        "rights_status": "unknown",
                        "provider": video.provider,
                    },
                )
        return list(sounds.values())

    def get_sound_videos(self, sound_id: str) -> list[ProviderVideo]:
        return [video for video in self._videos.values() if video.sound_id == sound_id]

    def health_check(self) -> dict[str, Any]:
        issues = self.settings.configuration_issues()
        return {
            "ok": not issues,
            "provider": f"apify:{self.settings.primary_actor_id}",
            "enabled": self.settings.enabled,
            "mode": self.settings.provider_mode,
            "token_configured": bool(self.settings.token.get_secret_value()),
            "primary_actor_id": self.settings.primary_actor_id,
            "fallback_actor_id": self.settings.fallback_actor_id,
            "fallback_enabled": self.settings.enable_fallback,
            "fallback_max_total_charge_usd": self.settings.fallback_max_total_charge_usd,
            "discover_actor_id": self.settings.discover_actor_id,
            "discover_enabled": self.settings.enable_discover,
            "default_market": self.settings.default_market,
            "supported_markets": list(self.settings.supported_markets),
            "configuration_issues": issues,
            "network_check": "not_run",
            "capabilities": provider_capabilities(self.settings).as_dict(),
        }

    async def network_health_check(self) -> dict[str, object]:
        issues = self.settings.configuration_issues()
        if issues:
            return {"ok": False, "network_check": "not_run", "configuration_issues": issues}
        return await asyncio.to_thread(self._client.health_check)

    def _effective_request(self, request: ActorRequest) -> ActorRequest:
        if self.max_items is None:
            return request
        maximum_result_count = min(request.maximum_result_count, max(1, self.max_items))
        payload = dict(request.payload)
        if request.contract == ActorContract.API_DOJO:
            payload["maxItems"] = maximum_result_count
        return replace(
            request,
            maximum_result_count=maximum_result_count,
            payload=payload,
        )

    def _estimate(self, request: ActorRequest, *, fallback: bool = False) -> CostEstimate:
        return estimate_cost(
            request,
            monthly_budget_usd=self.settings.monthly_budget_usd,
            monthly_spend_usd=self.monthly_spend_usd,
            explicit_run_cap_usd=(
                self.explicit_fallback_cap_usd if fallback else self.explicit_run_cap_usd
            ),
        )

    def _fallback_allowed(self, request: ActorRequest) -> bool:
        return (
            self.settings.enable_fallback
            and request.actor_id == self.settings.primary_actor_id
            and request.contract == ActorContract.API_DOJO
            and self.settings.fallback_actor_id != request.actor_id
            and request.collection_type != CollectionType.DISCOVER_EXPANSION
        )

    def _fallback_request(self, request: ActorRequest) -> ActorRequest:
        if request.collection_type == CollectionType.KEYWORD:
            return build_keyword_request(
                actor_id=self.settings.fallback_actor_id,
                keywords=request.source_values,
                market=request.market,
                supported_markets=self.settings.supported_markets,
                result_limit=request.result_limit_per_source,
                maximum_per_query=self.settings.max_results_per_query,
                date_range=request.date_range or SearchDateRange.PAST_WEEK,
                language=request.language,
                contract=ActorContract.CLOCKWORKS,
            )
        if request.collection_type == CollectionType.HASHTAG:
            return build_hashtag_request(
                actor_id=self.settings.fallback_actor_id,
                hashtags=request.source_values,
                market=request.market,
                supported_markets=self.settings.supported_markets,
                result_limit=request.result_limit_per_source,
                maximum_per_query=self.settings.max_results_per_query,
                language=request.language,
                contract=ActorContract.CLOCKWORKS,
            )
        if request.collection_type == CollectionType.PROFILE:
            return build_profile_request(
                actor_id=self.settings.fallback_actor_id,
                profiles=request.source_values,
                market=request.market,
                supported_markets=self.settings.supported_markets,
                result_limit=request.result_limit_per_source,
                maximum_per_query=self.settings.max_results_per_query,
                enrichment=False,
                language=request.language,
                contract=ActorContract.CLOCKWORKS,
            )
        if request.collection_type == CollectionType.DIRECT_REFRESH:
            return build_direct_refresh_request(
                actor_id=self.settings.fallback_actor_id,
                video_urls=request.source_values,
                market=request.market,
                supported_markets=self.settings.supported_markets,
                maximum_urls=self.settings.max_results_per_query,
                language=request.language,
                contract=ActorContract.CLOCKWORKS,
            )
        raise ApifyConfigurationError(
            "No Clockworks fallback exists for this collection type",
            context=ErrorContext(category="unsupported_fallback_collection"),
        )

    @staticmethod
    def _run_sync(coroutine: Any) -> Any:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coroutine)
        raise RuntimeError("Use the provider's async method from an active event loop")
