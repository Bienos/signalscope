from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.db import Base
from app.models import Snapshot, Video
from app.providers.apify import (
    ACTOR_ID,
    API_DOJO_ACTOR_ID,
    CLOCKWORKS_ACTOR_ID,
    DISCOVER_ACTOR_ID,
    PROFILE_ACTOR_ID,
    ApifyClientAdapter,
    ApifyAuthenticationError,
    ApifyBudgetError,
    ApifyConfigurationError,
    ApifyRunFailedError,
    ApifyTikTokProvider,
    ApifyTimeoutError,
    SearchDateRange,
    build_keyword_request,
    estimate_cost,
    normalize_items,
    safety_assertions,
)
from app.providers.factory import provider_factory
from app.services.pipeline import ingest, score_all


FIXTURE = Path(__file__).parent / "fixtures" / "apify_tiktok_items.json"
API_DOJO_FIXTURE = Path(__file__).parent / "fixtures" / "apidojo_tiktok_items.json"
TOKEN = "synthetic-test-token"


def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return sessionmaker(engine)()


def fixture_items() -> list[dict[str, Any]]:
    value = json.loads(FIXTURE.read_text())
    assert isinstance(value, list)
    return value


def api_dojo_fixture_items() -> list[dict[str, Any]]:
    value = json.loads(API_DOJO_FIXTURE.read_text())
    assert isinstance(value, list)
    return value


def run_response(status: str, *, run_id: str = "run-1", dataset_id: str = "dataset-1") -> dict:
    return {
            "id": run_id,
            "actId": "actor-1",
            "status": status,
            "statusMessage": "Synthetic run",
            "defaultDatasetId": dataset_id,
            "buildId": "build-1",
            "buildNumber": "1.2.3",
            "usageTotalUsd": 0.01,
            "startedAt": "2026-07-13T08:00:00Z",
            "finishedAt": "2026-07-13T08:00:02Z" if status == "SUCCEEDED" else None,
    }


class FakeActorClient:
    def __init__(self, owner: "FakeApifyClient", actor_id: str) -> None:
        self.owner = owner
        self.actor_id = actor_id

    def call(self, **kwargs: Any) -> dict[str, Any] | None:
        self.owner.seen.append({"actor_id": self.actor_id, **kwargs})
        if self.owner.error is not None:
            raise self.owner.error
        return run_response(self.owner.status)


class FakeDatasetClient:
    def __init__(self, owner: "FakeApifyClient", dataset_id: str) -> None:
        self.owner = owner
        self.dataset_id = dataset_id

    def iterate_items(self, **kwargs: Any):
        self.owner.seen.append({"dataset_id": self.dataset_id, **kwargs})
        yield from self.owner.items[: kwargs.get("limit")]


class FakeUserClient:
    def __init__(self, owner: "FakeApifyClient") -> None:
        self.owner = owner

    def get(self) -> dict[str, str]:
        if self.owner.error is not None:
            raise self.owner.error
        return {"id": "synthetic-user"}


class FakeApifyClient:
    def __init__(
        self,
        *,
        items: list[object] | None = None,
        status: str = "SUCCEEDED",
        error: Exception | None = None,
    ) -> None:
        self.items = fixture_items() if items is None else items
        self.status = status
        self.error = error
        self.seen: list[dict[str, Any]] = []

    def actor(self, actor_id: str) -> FakeActorClient:
        return FakeActorClient(self, actor_id)

    def dataset(self, dataset_id: str) -> FakeDatasetClient:
        return FakeDatasetClient(self, dataset_id)

    def user(self) -> FakeUserClient:
        return FakeUserClient(self)


class RoutingFakeActorClient:
    def __init__(self, owner: "RoutingFakeApifyClient", actor_id: str) -> None:
        self.owner = owner
        self.actor_id = actor_id

    def call(self, **kwargs: Any) -> dict[str, Any]:
        self.owner.seen.append({"actor_id": self.actor_id, **kwargs})
        error = self.owner.actor_errors.get(self.actor_id)
        if error is not None:
            raise error
        dataset_id = f"dataset-{self.actor_id.split('/')[0]}"
        self.owner.dataset_actors[dataset_id] = self.actor_id
        return run_response(
            "SUCCEEDED", run_id=f"run-{self.actor_id.split('/')[0]}", dataset_id=dataset_id
        )


class RoutingFakeDatasetClient:
    def __init__(self, owner: "RoutingFakeApifyClient", dataset_id: str) -> None:
        self.owner = owner
        self.dataset_id = dataset_id

    def iterate_items(self, **kwargs: Any):
        self.owner.seen.append({"dataset_id": self.dataset_id, **kwargs})
        actor_id = self.owner.dataset_actors[self.dataset_id]
        yield from self.owner.actor_items[actor_id][: kwargs.get("limit")]


class RoutingFakeApifyClient:
    def __init__(
        self,
        *,
        actor_items: dict[str, list[object]],
        actor_errors: dict[str, Exception] | None = None,
    ) -> None:
        self.actor_items = actor_items
        self.actor_errors = actor_errors or {}
        self.dataset_actors: dict[str, str] = {}
        self.seen: list[dict[str, Any]] = []

    def actor(self, actor_id: str) -> RoutingFakeActorClient:
        return RoutingFakeActorClient(self, actor_id)

    def dataset(self, dataset_id: str) -> RoutingFakeDatasetClient:
        return RoutingFakeDatasetClient(self, dataset_id)

    def user(self) -> FakeUserClient:
        return FakeUserClient(self)  # type: ignore[arg-type]


def provider_with_transport(
    seen: list[dict[str, Any]], *, items: list[object] | None = None
) -> ApifyTikTokProvider:
    fake = FakeApifyClient(items=items)
    fake.seen = seen

    return ApifyTikTokProvider(
        token=TOKEN,
        enabled=True,
        provider_mode="live",
        search_queries=["sensory toys"],
        results_per_page=10,
        max_items=20,
        max_total_charge_usd=0.5,
        actor_id=CLOCKWORKS_ACTOR_ID,
        enable_fallback=False,
        enable_discover=True,
        client=fake,
    )


def test_typed_inputs_are_scoped_and_force_expensive_collection_off() -> None:
    seen: list[dict[str, Any]] = []
    provider = provider_with_transport(seen)
    request = provider.keyword_request(
        ["sensory toys"], result_limit=10, date_range=SearchDateRange.PAST_WEEK
    )
    preflight = provider.preflight(request)

    assert preflight["actor_id"] == CLOCKWORKS_ACTOR_ID
    assert preflight["maximum_result_count"] == 10
    assert preflight["safe_to_execute"] is True
    assert TOKEN not in json.dumps(preflight)
    payload = preflight["actor_payload"]
    assert isinstance(payload, dict)
    assert payload["searchQueries"] == ["sensory toys"]
    assert payload["searchSection"] == "/video"
    assert payload["videoSearchSorting"] == "LATEST"
    assert payload["videoSearchDateFilter"] == "PAST_WEEK"
    assert payload["proxyCountryCode"] == "GB"
    assert payload["maxFollowersPerProfile"] == 0
    assert payload["maxFollowingPerProfile"] == 0
    assert payload["commentsPerPost"] == 0
    assert payload["downloadSubtitlesOptions"] == "NEVER_DOWNLOAD_SUBTITLES"
    assert safety_assertions(request) == {
        "media_downloads_disabled": True,
        "subtitles_and_transcripts_disabled": True,
        "comments_disabled": True,
        "follower_lists_disabled": True,
        "additional_author_metadata_disabled": True,
        "related_expansion_disabled": True,
    }
    assert seen == []


def test_api_dojo_is_default_primary_with_documented_inputs_and_safe_normalization() -> None:
    seen: list[dict[str, Any]] = []
    fake = FakeApifyClient(items=api_dojo_fixture_items())
    fake.seen = seen
    provider = ApifyTikTokProvider(
        token=TOKEN,
        enabled=True,
        provider_mode="live",
        results_per_page=10,
        max_items=20,
        max_total_charge_usd=0.50,
        client=fake,
    )
    request = provider.keyword_request(
        ["sensory toys"], result_limit=10, date_range=SearchDateRange.PAST_MONTH
    )
    preflight = provider.preflight(request)
    assert preflight["actor_id"] == API_DOJO_ACTOR_ID
    assert preflight["actor_payload"] == {
        "keywords": ["sensory toys"],
        "sortType": "DATE_POSTED",
        "location": "GB",
        "dateRange": "THIS_MONTH",
        "maxItems": 10,
        "includeSearchKeywords": True,
    }
    assert preflight["safe_to_execute"] is True
    assert preflight["maximum_combined_charge_usd"] == 1.0

    videos = provider.collect_sync(request)
    assert len(videos) == 1
    video = videos[0]
    assert video.provider == f"apify:{API_DOJO_ACTOR_ID}"
    assert video.metrics["views"] == 340916
    assert video.metrics["saves"] == 1141
    assert video.creator_id == "208464585232822272"
    assert video.username == "toylab"
    assert video.hashtags == ["sensorytoys", "toyreview"]
    assert video.sound_id == "7546234520153624000"
    assert video.duration_seconds == 60
    assert video.creator_account_region is None
    assert video.market == "GB"
    assert video.normalizer_version == "apify-toy-1.3"
    serialized = json.dumps(asdict(video), default=str)
    assert "media.invalid" not in serialized
    assert "subtitleInformation" not in serialized
    assert seen[0]["actor_id"] == API_DOJO_ACTOR_ID


def test_api_dojo_hashtag_profile_and_direct_inputs_use_documented_start_urls() -> None:
    provider = ApifyTikTokProvider(
        token=TOKEN, enabled=True, provider_mode="live", client=FakeApifyClient()
    )
    hashtag = provider.hashtag_request(["#sensory toys"], result_limit=5)
    profile = provider.profile_request(["@toylab"], result_limit=5)
    video_url = "https://www.tiktok.com/@toylab/video/7546234572208377101"
    direct = provider.direct_refresh_request([video_url])
    assert hashtag.payload["startUrls"] == [
        "https://www.tiktok.com/tag/sensory%20toys"
    ]
    assert profile.payload["startUrls"] == ["https://www.tiktok.com/@toylab"]
    assert direct.payload["startUrls"] == [video_url]
    assert all(safety_assertions(hashtag).values())
    assert all(safety_assertions(profile).values())
    assert all(safety_assertions(direct).values())


def test_clockworks_runs_only_after_retryable_api_dojo_failure() -> None:
    fake = RoutingFakeApifyClient(
        actor_items={
            API_DOJO_ACTOR_ID: api_dojo_fixture_items(),
            CLOCKWORKS_ACTOR_ID: fixture_items()[:1],
        },
        actor_errors={API_DOJO_ACTOR_ID: TimeoutError("synthetic API Dojo timeout")},
    )
    provider = ApifyTikTokProvider(
        token=TOKEN,
        enabled=True,
        provider_mode="live",
        results_per_page=5,
        max_total_charge_usd=0.50,
        fallback_max_total_charge_usd=0.50,
        client=fake,
    )
    videos = provider.collect_sync(provider.keyword_request(["sensory toys"]))
    assert len(videos) == 1
    actor_calls = [record for record in fake.seen if "actor_id" in record]
    assert [record["actor_id"] for record in actor_calls] == [
        API_DOJO_ACTOR_ID,
        CLOCKWORKS_ACTOR_ID,
    ]
    assert str(actor_calls[0]["max_total_charge_usd"]) == "0.5"
    assert str(actor_calls[1]["max_total_charge_usd"]) == "0.5"
    assert provider.last_run_quality["fallback_used"] is True
    assert provider.last_run_quality["primary_actor_id"] == API_DOJO_ACTOR_ID
    assert provider.last_run_quality["fallback_actor_id"] == CLOCKWORKS_ACTOR_ID
    assert provider.last_run_quality["primary_failure_category"] == "actor_call"
    assert videos[0].provider == f"apify:{CLOCKWORKS_ACTOR_ID}"


def test_api_dojo_demo_only_records_use_clockworks_fallback() -> None:
    fake = RoutingFakeApifyClient(
        actor_items={
            API_DOJO_ACTOR_ID: [{"demo": True}],
            CLOCKWORKS_ACTOR_ID: fixture_items()[:1],
        }
    )
    provider = ApifyTikTokProvider(
        token=TOKEN,
        enabled=True,
        provider_mode="live",
        max_total_charge_usd=0.50,
        fallback_max_total_charge_usd=0.50,
        client=fake,
    )

    videos = provider.collect_sync(provider.keyword_request(["sensory toys"]))

    assert len(videos) == 1
    assert videos[0].provider == f"apify:{CLOCKWORKS_ACTOR_ID}"
    assert provider.last_run_quality["fallback_used"] is True
    assert provider.last_run_quality["primary_failure_category"] == "provider_demo_mode"


def test_clockworks_does_not_run_after_api_dojo_success() -> None:
    fake = RoutingFakeApifyClient(
        actor_items={
            API_DOJO_ACTOR_ID: api_dojo_fixture_items(),
            CLOCKWORKS_ACTOR_ID: fixture_items()[:1],
        }
    )
    provider = ApifyTikTokProvider(
        token=TOKEN, enabled=True, provider_mode="live", client=fake
    )
    videos = provider.collect_sync(provider.keyword_request(["sensory toys"]))
    assert len(videos) == 1
    actor_calls = [record for record in fake.seen if "actor_id" in record]
    assert [record["actor_id"] for record in actor_calls] == [API_DOJO_ACTOR_ID]
    assert provider.last_run_quality["fallback_used"] is False


def test_clockworks_does_not_run_for_shared_authentication_failure() -> None:
    class AuthenticationError(RuntimeError):
        status_code = 401

    fake = RoutingFakeApifyClient(
        actor_items={
            API_DOJO_ACTOR_ID: api_dojo_fixture_items(),
            CLOCKWORKS_ACTOR_ID: fixture_items()[:1],
        },
        actor_errors={API_DOJO_ACTOR_ID: AuthenticationError("invalid token")},
    )
    provider = ApifyTikTokProvider(
        token=TOKEN, enabled=True, provider_mode="live", client=fake
    )
    with pytest.raises(ApifyAuthenticationError):
        provider.collect_sync(provider.keyword_request(["sensory toys"]))
    actor_calls = [record for record in fake.seen if "actor_id" in record]
    assert [record["actor_id"] for record in actor_calls] == [API_DOJO_ACTOR_ID]


def test_safety_assertions_fail_closed_when_an_explicit_control_is_missing() -> None:
    provider = provider_with_transport([])
    request = provider.keyword_request(["sensory toys"], result_limit=5)
    controls = {
        "shouldDownloadVideos": "media_downloads_disabled",
        "downloadSubtitlesOptions": "subtitles_and_transcripts_disabled",
        "commentsPerPost": "comments_disabled",
        "maxFollowersPerProfile": "follower_lists_disabled",
        "scrapeAdditionalAuthorMeta": "additional_author_metadata_disabled",
        "scrapeRelatedVideos": "related_expansion_disabled",
    }
    for input_name, assertion_name in controls.items():
        incomplete = replace(
            request,
            payload={
                key: value for key, value in request.payload.items() if key != input_name
            },
        )
        assert safety_assertions(incomplete)[assertion_name] is False
        assert provider.preflight(incomplete)["safe_to_execute"] is False


def test_async_start_poll_and_normalization_keep_provenance_without_media() -> None:
    seen: list[dict[str, Any]] = []
    provider = provider_with_transport(seen)
    videos = provider.collect_sync(provider.keyword_request(["sensory toys"], result_limit=10))

    assert len(videos) == 2
    video = videos[0]
    assert video.provider == f"apify:{CLOCKWORKS_ACTOR_ID}"
    assert video.provider_run_id == "run-1"
    assert video.dataset_id == "dataset-1"
    assert video.market == "GB"
    assert video.creator_account_region == "GB"
    assert video.creator_followers == 12500
    assert video.metrics == {
        "views": 125000,
        "likes": 12500,
        "comments": 340,
        "shares": 850,
        "saves": 1200,
        "favourites": 1200,
    }
    assert video.hashtags == ["sensorytoys", "toyreview"]
    assert video.sound_id == "sound-101"
    assert video.duration_seconds == 19
    assert video.normalizer_version == "apify-toy-1.3"
    serialized = json.dumps(asdict(video), default=str)
    assert "media.invalid" not in serialized
    assert "This must not be mapped" not in serialized
    assert seen[0]["actor_id"] == CLOCKWORKS_ACTOR_ID
    assert seen[0]["max_items"] == 10
    assert str(seen[0]["max_total_charge_usd"]) == "0.5"
    assert seen[1]["dataset_id"] == "dataset-1"
    assert TOKEN not in json.dumps(seen, default=str)


def test_clockworks_fractional_video_duration_is_normalized_to_seconds() -> None:
    seen: list[dict[str, Any]] = []
    items = fixture_items()[:1]
    items[0]["videoMeta"]["duration"] = 29.001
    provider = provider_with_transport(seen, items=items)

    videos = provider.collect_sync(
        provider.keyword_request(["sensory toys"], result_limit=1)
    )

    assert len(videos) == 1
    assert videos[0].duration_seconds == 29
    assert videos[0].normalizer_version == "apify-toy-1.3"


def test_collection_market_is_context_not_creator_account_region() -> None:
    seen: list[dict[str, Any]] = []
    provider = provider_with_transport(seen)
    partial = provider.collect_sync(provider.keyword_request(["STEM toys"]))[1]
    assert partial.market == "GB"
    assert partial.creator_account_region is None
    assert "creator_account_region" in partial.missing_fields
    assert "market" not in partial.missing_fields
    assert partial.metrics["views"] is None
    assert partial.metrics["saves"] is None


def test_direct_refresh_and_profiles_use_only_the_primary_actor() -> None:
    seen: list[dict[str, Any]] = []
    provider = provider_with_transport(seen)
    url = "https://www.tiktok.com/@toytester/video/7411111111111111111"
    direct = provider.direct_refresh_request([url])
    assert direct.payload["postURLs"] == [url]
    assert "searchQueries" not in direct.payload
    assert direct.maximum_result_count == 1

    profile = provider.profile_request(["@toytester"])
    assert profile.actor_id == CLOCKWORKS_ACTOR_ID
    assert profile.payload["profiles"] == ["toytester"]
    assert profile.payload["profileScrapeSections"] == ["videos"]
    with pytest.raises(ApifyConfigurationError):
        provider.profile_request(["toytester"], use_enrichment_actor=True)

    assert PROFILE_ACTOR_ID == ACTOR_ID == API_DOJO_ACTOR_ID


def test_discover_actor_is_hashtag_only_and_omits_unsupported_controls() -> None:
    provider = provider_with_transport([])
    request = provider.discover_expansion_request(["#sensorytoys"], result_limit=4)
    assert request.actor_id == DISCOVER_ACTOR_ID
    assert request.payload == {
        "hashtags": ["sensorytoys"],
        "resultsPerPage": 4,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False,
        "shouldDownloadSlideshowImages": False,
        "downloadSubtitlesOptions": "NEVER_DOWNLOAD_SUBTITLES",
    }
    assert all(safety_assertions(request).values())


def test_discover_output_preserves_normalized_expansion_context() -> None:
    item = dict(fixture_items()[0])
    item["discoveryInfo"] = {
        "tag": "sensorytoys",
        "relatedTags": ["stemtoys", {"name": "fidgettoys"}],
        "type": "discover",
        "url": "https://www.tiktok.com/discover/sensorytoys",
    }
    provider = ApifyTikTokProvider(
        token=TOKEN,
        enabled=True,
        provider_mode="live",
        enable_discover=True,
        client=FakeApifyClient(items=[item]),
    )
    video = provider.collect_sync(
        provider.discover_expansion_request(["sensorytoys"], result_limit=1)
    )[0]
    assert video.discovery_context == {
        "seed": "sensorytoys",
        "related_terms": ["stemtoys", "fidgettoys"],
        "discovery_type": "discover",
    }
    assert provider.last_run_quality["related_discovery_terms"] == [
        "fidgettoys",
        "stemtoys",
    ]


def test_hashtag_builder_is_scoped_and_direct_refresh_rejects_lookalike_hosts() -> None:
    provider = provider_with_transport([])
    hashtag = provider.hashtag_request(["#toytok", "sensorytoys"], result_limit=4)
    assert hashtag.payload["hashtags"] == ["toytok", "sensorytoys"]
    assert hashtag.maximum_result_count == 8
    assert "searchQueries" not in hashtag.payload
    assert all(safety_assertions(hashtag).values())

    with pytest.raises(ValueError, match="canonical HTTPS TikTok URLs"):
        provider.direct_refresh_request(
            ["https://not-tiktok.com/@toytester/video/7411111111111111111"]
        )


def test_missing_metrics_remain_null_and_are_not_scored() -> None:
    seen: list[dict[str, Any]] = []
    provider = provider_with_transport(seen)
    partial = provider.collect_sync(provider.keyword_request(["STEM toys"]))[1]
    session = db()
    first = datetime(2026, 7, 12, 12)
    ingest(session, [partial], first)
    ingest(session, [partial], first + timedelta(hours=6))
    snapshots = session.scalars(select(Snapshot).order_by(Snapshot.collected_at)).all()
    assert len(snapshots) == 2
    assert all(snapshot.views is None for snapshot in snapshots)
    assert score_all(session) == 0


def test_ingestion_persists_reference_and_appends_snapshots() -> None:
    seen: list[dict[str, Any]] = []
    provider = provider_with_transport(seen)
    full = provider.collect_sync(provider.keyword_request(["sensory toys"]))[0]
    session = db()
    first = datetime(2026, 7, 12, 12)
    ingest(session, [full], first)
    full.metrics["views"] = 150000
    ingest(session, [full], first + timedelta(hours=6))
    video = session.scalar(select(Video).where(Video.provider_id == full.id))
    assert video is not None
    assert "runs/run-1/datasets/dataset-1" in video.raw_reference
    snapshots = session.scalars(
        select(Snapshot).where(Snapshot.video_id == video.id).order_by(Snapshot.collected_at)
    ).all()
    assert [snapshot.views for snapshot in snapshots] == [125000, 150000]


def test_official_client_adapter_uses_paginating_dataset_iterator() -> None:
    fake = FakeApifyClient(items=[{"id": index} for index in range(3)])
    client = ApifyClientAdapter(token=TOKEN, client=fake)
    health = client.health_check()
    items = client.get_dataset_items("dataset", maximum_items=3)
    assert health["ok"] is True
    assert items == [{"id": 0}, {"id": 1}, {"id": 2}]
    assert fake.seen == [{"dataset_id": "dataset", "limit": 3, "clean": True}]


def test_authentication_errors_redact_token() -> None:
    class AuthenticationError(RuntimeError):
        status_code = 401

    client = ApifyClientAdapter(
        token=TOKEN,
        client=FakeApifyClient(error=AuthenticationError(f"Invalid credential {TOKEN}")),
    )
    with pytest.raises(ApifyAuthenticationError) as captured:
        client.health_check()
    assert TOKEN not in str(captured.value)
    assert "[REDACTED]" in str(captured.value)


def test_official_client_timeout_is_translated_without_leaking_credentials() -> None:
    request = build_keyword_request(
        actor_id=CLOCKWORKS_ACTOR_ID,
        keywords=["toy trend"],
        market="GB",
        supported_markets=("GB", "PL"),
        result_limit=5,
        maximum_per_query=50,
    )
    estimate = estimate_cost(request, monthly_budget_usd=50)
    client = ApifyClientAdapter(
        token=TOKEN,
        client=FakeApifyClient(error=TimeoutError(f"synthetic timeout {TOKEN}")),
    )
    with pytest.raises(ApifyTimeoutError) as captured:
        client.run_actor(request, estimate)
    assert TOKEN not in str(captured.value)


def test_invalid_and_provider_error_items_are_quarantined_without_raw_retention() -> None:
    request = build_keyword_request(
        actor_id=CLOCKWORKS_ACTOR_ID,
        keywords=["sensory toys"],
        market="GB",
        supported_markets=("GB", "PL"),
        result_limit=5,
        maximum_per_query=50,
    )
    invalid_items: list[object] = [
        fixture_items()[0],
        "not-an-object",
        {"errorCode": "private-video", "error": "Video is private"},
        {"id": "missing-identities"},
    ]
    result = normalize_items(
        invalid_items,
        request=request,
        run_id="run-1",
        dataset_id="dataset-1",
        retrieved_at=datetime(2026, 7, 13, 8),
        secrets=[TOKEN],
    )
    assert len(result.videos) == 1
    assert len(result.quarantined) == 3
    assert {item.category for item in result.quarantined} == {
        "invalid_record",
        "private_video",
        "missing_identity",
    }
    assert all(TOKEN not in item.summary for item in result.quarantined)


def test_last_run_quality_uses_typed_quarantine_persistence_contract() -> None:
    seen: list[dict[str, Any]] = []
    provider = provider_with_transport(
        seen,
        items=[
            fixture_items()[0],
            "not-an-object",
            {"errorCode": "private-video", "error": f"private {TOKEN}"},
        ],
    )

    videos = provider.collect_sync(provider.keyword_request(["sensory toys"]))

    assert len(videos) == 1
    records = provider.last_run_quality["quarantine"]
    assert [record["record_index"] for record in records] == [1, 2]
    assert [record["external_record_id"] for record in records] == [
        "dataset-item:1",
        "dataset-item:2",
    ]
    assert {record["reason"] for record in records} == {
        "invalid_record",
        "private_video",
    }
    assert all(
        set(record)
        == {
            "external_record_id",
            "record_index",
            "reason",
            "summary",
            "schema_fingerprint",
            "missing_fields",
        }
        for record in records
    )
    assert TOKEN not in json.dumps(records)


def test_failed_run_with_usable_dataset_is_explicit_partial_success() -> None:
    provider = ApifyTikTokProvider(
        token=TOKEN,
        enabled=True,
        provider_mode="live",
        results_per_page=5,
        actor_id=CLOCKWORKS_ACTOR_ID,
        enable_fallback=False,
        client=FakeApifyClient(items=fixture_items()[:1], status="FAILED"),
    )
    videos = provider.collect_sync(provider.keyword_request(["sensory toys"]))
    assert len(videos) == 1
    assert provider.last_run_quality["status"] == "failed"
    assert provider.last_run_quality["partial_dataset"] is True


def test_failed_run_without_usable_dataset_raises_structured_error() -> None:
    provider = ApifyTikTokProvider(
        token=TOKEN,
        enabled=True,
        provider_mode="live",
        actor_id=CLOCKWORKS_ACTOR_ID,
        enable_fallback=False,
        client=FakeApifyClient(items=[], status="FAILED"),
    )
    with pytest.raises(ApifyRunFailedError) as captured:
        provider.collect_sync(provider.keyword_request(["sensory toys"]))
    assert captured.value.context.category == "actor_run_failed"


def test_cost_preflight_enforces_run_and_monthly_caps_without_network() -> None:
    provider = ApifyTikTokProvider(
        token=TOKEN,
        enabled=True,
        provider_mode="live",
        monthly_budget_usd=0.75,
        monthly_spend_usd=0.25,
        max_total_charge_usd=1.0,
    )
    request = provider.keyword_request(["sensory toys"], result_limit=5)
    cost = provider.preflight(request)["cost"]
    assert isinstance(cost, dict)
    assert cost["enforced_max_charge_usd"] == 0.5

    exhausted = ApifyTikTokProvider(
        token=TOKEN,
        enabled=True,
        provider_mode="live",
        monthly_budget_usd=0.5,
        monthly_spend_usd=0.5,
    )
    with pytest.raises(ApifyBudgetError):
        exhausted.preflight(exhausted.keyword_request(["sensory toys"], result_limit=5))


def test_factory_keeps_apify_disabled_in_default_demo_mode() -> None:
    config = Settings(_env_file=None, provider_type="apify", apify_enabled=False)
    provider = provider_factory(config)
    health = provider.health_check()
    assert health["ok"] is False
    assert health["mode"] == "demo"
    with pytest.raises(ApifyConfigurationError):
        provider.discover_videos()
