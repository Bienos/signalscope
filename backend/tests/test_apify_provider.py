from __future__ import annotations

import asyncio
from dataclasses import asdict, replace
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Any

import httpx
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.db import Base
from app.models import Snapshot, Video
from app.providers.apify import (
    ACTOR_ID,
    PROFILE_ACTOR_ID,
    ApifyAsyncClient,
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
TOKEN = "synthetic-test-token"


def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return sessionmaker(engine)()


def fixture_items() -> list[dict[str, Any]]:
    value = json.loads(FIXTURE.read_text())
    assert isinstance(value, list)
    return value


def run_response(status: str, *, run_id: str = "run-1", dataset_id: str = "dataset-1") -> dict:
    return {
        "data": {
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
    }


def provider_with_transport(
    seen: list[dict[str, Any]], *, items: list[object] | None = None
) -> ApifyTikTokProvider:
    dataset = fixture_items() if items is None else items

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else None
        seen.append(
            {
                "method": request.method,
                "authorization": request.headers.get("authorization"),
                "url": str(request.url),
                "path": request.url.path,
                "params": dict(request.url.params),
                "body": body,
            }
        )
        if request.method == "POST" and request.url.path.endswith("/runs"):
            return httpx.Response(201, json=run_response("READY"))
        if "/actor-runs/" in request.url.path:
            return httpx.Response(200, json=run_response("SUCCEEDED"))
        if "/datasets/" in request.url.path:
            offset = int(request.url.params.get("offset", "0"))
            limit = int(request.url.params.get("limit", "1000"))
            return httpx.Response(200, json=dataset[offset : offset + limit])
        return httpx.Response(404, json={"error": {"message": "Unexpected synthetic URL"}})

    return ApifyTikTokProvider(
        token=TOKEN,
        enabled=True,
        provider_mode="live",
        search_queries=["sensory toys"],
        results_per_page=10,
        max_items=20,
        max_total_charge_usd=0.5,
        poll_interval_seconds=0,
        transport=httpx.MockTransport(handler),
    )


def test_typed_inputs_are_scoped_and_force_expensive_collection_off() -> None:
    seen: list[dict[str, Any]] = []
    provider = provider_with_transport(seen)
    request = provider.keyword_request(
        ["sensory toys"], result_limit=10, date_range=SearchDateRange.PAST_WEEK
    )
    preflight = provider.preflight(request)

    assert preflight["actor_id"] == ACTOR_ID
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
    assert video.provider == f"apify:{ACTOR_ID}"
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
    assert video.normalizer_version == "apify-toy-1.0"
    serialized = json.dumps(asdict(video), default=str)
    assert "media.invalid" not in serialized
    assert "This must not be mapped" not in serialized
    assert seen[0]["authorization"] == f"Bearer {TOKEN}"
    assert TOKEN not in seen[0]["url"]
    assert seen[0]["params"]["maxItems"] == "10"
    assert seen[0]["params"]["maxTotalChargeUsd"] == "0.5"
    assert any("/actor-runs/run-1" in item["path"] for item in seen)
    assert any("/datasets/dataset-1/items" in item["path"] for item in seen)


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


def test_direct_refresh_and_optional_profile_actor_are_explicit() -> None:
    seen: list[dict[str, Any]] = []
    provider = provider_with_transport(seen)
    url = "https://www.tiktok.com/@toytester/video/7411111111111111111"
    direct = provider.direct_refresh_request([url])
    assert direct.payload["postURLs"] == [url]
    assert "searchQueries" not in direct.payload
    assert direct.maximum_result_count == 1

    profile = provider.profile_request(["@toytester"])
    assert profile.actor_id == ACTOR_ID
    assert profile.payload["profiles"] == ["toytester"]
    assert profile.payload["profileScrapeSections"] == ["videos"]
    with pytest.raises(ApifyConfigurationError):
        provider.profile_request(["toytester"], use_enrichment_actor=True)

    enabled = ApifyTikTokProvider(
        token=TOKEN,
        enabled=True,
        profile_enrichment_enabled=True,
    )
    enrichment = enabled.profile_request(["toytester"], use_enrichment_actor=True)
    assert enrichment.actor_id == PROFILE_ACTOR_ID
    assert enrichment.collection_type.value == "profile_enrichment"
    assert all(safety_assertions(enrichment).values())
    assert "scrapeRelatedSearchWords" not in enrichment.payload
    assert "scrapeRelatedVideos" not in enrichment.payload
    assert "scrapeAdditionalAuthorMeta" not in enrichment.payload
    assert enrichment.payload["maxFollowersPerProfile"] == 0
    assert enrichment.payload["maxFollowingPerProfile"] == 0
    assert enrichment.payload["commentsPerPost"] == 0
    assert enrichment.payload["topLevelCommentsPerPost"] == 0
    assert enrichment.payload["maxRepliesPerComment"] == 0
    assert enrichment.payload["shouldDownloadVideos"] is False
    assert enrichment.payload["shouldDownloadCovers"] is False
    assert enrichment.payload["shouldDownloadSlideshowImages"] is False
    assert enrichment.payload["shouldDownloadAvatars"] is False
    assert "shouldDownloadMusicCovers" not in enrichment.payload
    assert enrichment.payload["downloadSubtitlesOptions"] == "NEVER_DOWNLOAD_SUBTITLES"
    incomplete_enrichment = replace(
        enrichment,
        payload={
            key: value
            for key, value in enrichment.payload.items()
            if key != "shouldDownloadVideos"
        },
    )
    assert safety_assertions(incomplete_enrichment)["media_downloads_disabled"] is False


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


def test_dataset_pagination_and_retry_after_are_handled_for_gets() -> None:
    calls: list[str] = []
    rate_limit_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal rate_limit_count
        calls.append(str(request.url))
        if request.url.path.endswith("/users/me"):
            rate_limit_count += 1
            if rate_limit_count == 1:
                return httpx.Response(429, headers={"Retry-After": "0"}, json={"error": {"message": "slow"}})
            return httpx.Response(200, json={"data": {"id": "synthetic-user"}})
        offset = int(request.url.params.get("offset", "0"))
        values = [{"id": index} for index in range(3)]
        return httpx.Response(200, json=values[offset : offset + 1])

    client = ApifyAsyncClient(
        token=TOKEN,
        poll_interval_seconds=0,
        dataset_page_size=1,
        transport=httpx.MockTransport(handler),
    )
    health = asyncio.run(client.health_check())
    items = asyncio.run(client.get_dataset_items("dataset", maximum_items=3))
    assert health["ok"] is True
    assert rate_limit_count == 2
    assert items == [{"id": 0}, {"id": 1}, {"id": 2}]
    assert sum("/datasets/dataset/items" in call for call in calls) == 3


def test_authentication_errors_redact_token() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401, json={"error": {"message": f"Invalid credential {TOKEN}"}}
        )

    client = ApifyAsyncClient(token=TOKEN, transport=httpx.MockTransport(handler))
    with pytest.raises(ApifyAuthenticationError) as captured:
        asyncio.run(client.health_check())
    assert TOKEN not in str(captured.value)
    assert "[REDACTED]" in str(captured.value)


def test_ambiguous_actor_start_timeout_is_not_retried() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("synthetic timeout", request=request)

    request = build_keyword_request(
        actor_id=ACTOR_ID,
        keywords=["toy trend"],
        market="GB",
        supported_markets=("GB", "PL"),
        result_limit=5,
        maximum_per_query=50,
    )
    estimate = estimate_cost(request, monthly_budget_usd=50)
    client = ApifyAsyncClient(token=TOKEN, transport=httpx.MockTransport(handler))
    with pytest.raises(ApifyTimeoutError) as captured:
        asyncio.run(client.start_run(request, estimate))
    assert calls == 1
    assert captured.value.context.category == "ambiguous_actor_start_timeout"


def test_invalid_and_provider_error_items_are_quarantined_without_raw_retention() -> None:
    request = build_keyword_request(
        actor_id=ACTOR_ID,
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
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(201, json=run_response("READY"))
        if "/actor-runs/" in request.url.path:
            return httpx.Response(200, json=run_response("FAILED"))
        if "/datasets/" in request.url.path:
            return httpx.Response(200, json=fixture_items()[:1])
        return httpx.Response(404)

    provider = ApifyTikTokProvider(
        token=TOKEN,
        enabled=True,
        provider_mode="live",
        results_per_page=5,
        poll_interval_seconds=0,
        transport=httpx.MockTransport(handler),
    )
    videos = provider.collect_sync(provider.keyword_request(["sensory toys"]))
    assert len(videos) == 1
    assert provider.last_run_quality["status"] == "failed"
    assert provider.last_run_quality["partial_dataset"] is True


def test_failed_run_without_usable_dataset_raises_structured_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            return httpx.Response(201, json=run_response("READY"))
        if "/actor-runs/" in request.url.path:
            return httpx.Response(200, json=run_response("FAILED"))
        if "/datasets/" in request.url.path:
            return httpx.Response(200, json=[])
        return httpx.Response(404)

    provider = ApifyTikTokProvider(
        token=TOKEN,
        enabled=True,
        provider_mode="live",
        poll_interval_seconds=0,
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(ApifyRunFailedError) as captured:
        provider.collect_sync(provider.keyword_request(["sensory toys"]))
    assert captured.value.context.category == "actor_run_failed"


def test_cost_preflight_enforces_run_and_monthly_caps_without_network() -> None:
    provider = ApifyTikTokProvider(
        token=TOKEN,
        enabled=True,
        provider_mode="live",
        monthly_budget_usd=0.25,
        monthly_spend_usd=0.20,
        max_total_charge_usd=1.0,
    )
    request = provider.keyword_request(["sensory toys"], result_limit=5)
    cost = provider.preflight(request)["cost"]
    assert isinstance(cost, dict)
    assert cost["enforced_max_charge_usd"] == 0.05

    exhausted = ApifyTikTokProvider(
        token=TOKEN,
        enabled=True,
        provider_mode="live",
        monthly_budget_usd=0.25,
        monthly_spend_usd=0.25,
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
