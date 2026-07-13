from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta
import json
from pathlib import Path

import httpx
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.db import Base
from app.models import Snapshot, Video
from app.providers.apify_tiktok import ACTOR_ID, ApifyTikTokProvider, PROVIDER_NAME
from app.providers.factory import provider_factory
from app.services.pipeline import ingest, score_all

FIXTURE = Path(__file__).parent / "fixtures" / "apify_tiktok_items.json"


def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return sessionmaker(engine)()


def fixture_items() -> list[dict]:
    value = json.loads(FIXTURE.read_text())
    assert isinstance(value, list)
    return value


def provider_with_transport(seen: list[dict]) -> ApifyTikTokProvider:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(
            {
                "authorization": request.headers.get("authorization"),
                "url": str(request.url),
                "body": json.loads(request.content),
            }
        )
        return httpx.Response(200, json=fixture_items())

    return ApifyTikTokProvider(
        token="synthetic-test-token",
        enabled=True,
        search_queries=["sensory toys"],
        hashtags=["#stemtoys"],
        profiles=["@toytester"],
        results_per_page=10,
        max_items=20,
        max_total_charge_usd=0.5,
        transport=httpx.MockTransport(handler),
    )


def test_actor_input_is_scoped_and_disables_expensive_or_media_features() -> None:
    seen: list[dict] = []
    provider = provider_with_transport(seen)
    videos = provider.discover_videos()
    assert len(videos) == 2
    request = seen[0]
    assert request["authorization"] == "Bearer synthetic-test-token"
    assert "synthetic-test-token" not in request["url"]
    assert f"/actors/{ACTOR_ID}/run-sync-get-dataset-items" in request["url"]
    payload = request["body"]
    assert payload["searchQueries"] == ["sensory toys"]
    assert payload["hashtags"] == ["stemtoys"]
    assert payload["profiles"] == ["toytester"]
    assert payload["searchSection"] == "/video"
    assert payload["profileScrapeSections"] == ["videos"]
    assert payload["maxFollowersPerProfile"] == 0
    assert payload["maxFollowingPerProfile"] == 0
    assert payload["commentsPerPost"] == 0
    assert payload["downloadSubtitlesOptions"] == "NEVER_DOWNLOAD_SUBTITLES"
    assert not any(
        payload[key]
        for key in (
            "shouldDownloadVideos",
            "shouldDownloadCovers",
            "shouldDownloadSlideshowImages",
            "shouldDownloadAvatars",
            "shouldDownloadMusicCovers",
        )
    )


def test_mapping_keeps_provenance_metadata_and_ignores_media_and_comment_bodies() -> None:
    seen: list[dict] = []
    video = provider_with_transport(seen).discover_videos()[0]
    assert video.provider == PROVIDER_NAME
    assert video.raw_reference == f"apify://{ACTOR_ID}/video/{video.id}"
    assert video.metrics == {
        "views": 125000,
        "likes": 12500,
        "comments": 340,
        "shares": 850,
        "favourites": 1200,
    }
    assert video.hashtags == ["sensorytoys", "toyreview"]
    assert video.sound_id == "sound-101"
    assert video.sound_title == "Original sound"
    serialized = json.dumps(asdict(video), default=str)
    assert "media.invalid" not in serialized
    assert "This must not be mapped" not in serialized


def test_missing_metrics_remain_null_and_are_not_scored() -> None:
    seen: list[dict] = []
    partial = provider_with_transport(seen).discover_videos()[1]
    assert partial.metrics["views"] is None
    assert partial.metrics["favourites"] is None
    assert {"views", "favourites", "market", "language", "sound_id"} <= set(
        partial.missing_fields
    )
    session = db()
    first = datetime(2026, 7, 12, 12)
    ingest(session, [partial], first)
    ingest(session, [partial], first + timedelta(hours=6))
    snapshots = session.scalars(select(Snapshot).order_by(Snapshot.collected_at)).all()
    assert len(snapshots) == 2
    assert all(snapshot.views is None for snapshot in snapshots)
    assert score_all(session) == 0


def test_direct_url_refresh_and_profile_discovery_use_supported_actor_inputs() -> None:
    seen: list[dict] = []
    provider = provider_with_transport(seen)
    url = "https://www.tiktok.com/@toytester/video/7411111111111111111"
    provider.refresh_video_urls([url])
    assert seen[-1]["body"]["postURLs"] == [url]
    assert "searchQueries" not in seen[-1]["body"]
    provider.get_creator_recent_videos("@toytester")
    assert seen[-1]["body"]["profiles"] == ["toytester"]
    assert seen[-1]["body"]["maxFollowersPerProfile"] == 0


def test_ingestion_persists_provider_reference_and_immutable_snapshots() -> None:
    seen: list[dict] = []
    full = provider_with_transport(seen).discover_videos()[0]
    session = db()
    first = datetime(2026, 7, 12, 12)
    ingest(session, [full], first)
    full.metrics["views"] = 150000
    ingest(session, [full], first + timedelta(hours=6))
    video = session.scalar(select(Video).where(Video.provider_id == full.id))
    assert video is not None
    assert video.raw_reference == full.raw_reference
    snapshots = session.scalars(
        select(Snapshot).where(Snapshot.video_id == video.id).order_by(Snapshot.collected_at)
    ).all()
    assert [snapshot.views for snapshot in snapshots] == [125000, 150000]


def test_factory_keeps_apify_disabled_by_default() -> None:
    config = Settings(_env_file=None, provider_type="apify", apify_enabled=False)
    provider = provider_factory(config)
    assert provider.health_check()["ok"] is False
    try:
        provider.discover_videos()
        assert False, "disabled provider must not start a paid Actor run"
    except RuntimeError as error:
        assert "disabled" in str(error).lower()
