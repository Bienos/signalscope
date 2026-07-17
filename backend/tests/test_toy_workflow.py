from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app import cli
from app.config import Settings
from app.db import Base
from app.domain.toys import load_toy_taxonomy
from app.models import Creator, ProviderRun, Snapshot, ToySignal, Video
from app.providers.apify import ApifyProviderSettings, ApifyTikTokProvider
from app.providers.mock import HASHTAG_FIXTURES, SIGNAL_TEMPLATES, MockProvider
from app.services.pipeline import ingest
from app.services.toy_intelligence import build_or_update_toy_signals


def database() -> Session:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return sessionmaker(engine)()


def test_toy_fixture_has_bounded_cross_market_evidence() -> None:
    rows = MockProvider().discover_videos()
    assert len(rows) == 48
    assert len(SIGNAL_TEMPLATES) == 12
    assert len({row.creator_id for row in rows}) == 20
    assert len({row.sound_id for row in rows}) == 8
    assert len({tag for row in rows for tag in row.hashtags}) == len(HASHTAG_FIXTURES) == 20
    assert {row.market for row in rows} == {"GB", "PL"}
    assert {row.language for row in rows} == {"en", "pl"}
    assert all("Synthetic demo" in row.caption for row in rows)
    assert all(row.provider == "mock" for row in rows)


def test_ingest_preserves_nulls_provenance_and_immutable_snapshots() -> None:
    db = database()
    first_observed = cli.utc_now() - timedelta(hours=6)
    first_run = ProviderRun(
        provider="mock",
        external_run_id="mock-run-0",
        started_at=first_observed,
        status="success",
    )
    db.add(first_run)
    db.commit()
    db.refresh(first_run)
    row = MockProvider(0).discover_videos(13)[-1]
    assert row.metrics["favourites"] is None

    first = ingest(
        db,
        [row],
        first_observed,
        provider_run_id=first_run.id,
        collection_market="PL",
    )
    assert first == {
        "new": 1,
        "duplicates": 0,
        "snapshots_added": 1,
        "snapshot_duplicates": 0,
        "total": 1,
    }
    video = db.scalar(select(Video).where(Video.provider_id == row.id))
    assert video is not None
    snapshot = db.scalar(select(Snapshot).where(Snapshot.video_id == video.id))
    creator = db.get(Creator, video.creator_id)
    assert snapshot is not None and creator is not None
    assert snapshot.favourites is None
    assert snapshot.provider_run_id == first_run.id
    assert video.provider_run_id == first_run.id
    assert video.collection_market == "PL"
    assert video.discovery_query["provider_external_run_id"] == "mock-run-0"
    assert video.schema_fingerprint == "mock-toy-schema-1"
    assert creator.followers == row.creator_followers
    assert creator.region == row.creator_account_region
    assert creator.apparent_minor is None
    assert video.child_featured is None

    # Reprocessing the same provider run must not mutate or append its observation.
    duplicate = ingest(
        db,
        [row],
        first_observed + timedelta(minutes=5),
        provider_run_id=first_run.id,
        collection_market="PL",
    )
    assert duplicate["snapshots_added"] == 0
    assert duplicate["snapshot_duplicates"] == 1
    assert db.query(Snapshot).count() == 1

    second_run = ProviderRun(
        provider="mock",
        external_run_id="mock-run-1",
        started_at=first_observed + timedelta(hours=6),
        status="success",
    )
    db.add(second_run)
    db.commit()
    db.refresh(second_run)
    refreshed = MockProvider(1).discover_videos(13)[-1]
    ingest(
        db,
        [refreshed],
        first_observed + timedelta(hours=6),
        provider_run_id=second_run.id,
        collection_market="PL",
    )
    snapshots = db.scalars(
        select(Snapshot)
        .where(Snapshot.video_id == video.id)
        .order_by(Snapshot.collected_at)
    ).all()
    assert len(snapshots) == 2
    assert snapshots[0].views != snapshots[1].views
    assert snapshots[0].favourites is None and snapshots[1].favourites is None


def test_ingest_scopes_colliding_external_ids_by_provider() -> None:
    db = database()
    observed_at = cli.utc_now()
    demo = MockProvider(0).discover_videos(1)[0]
    ingest(db, [demo], observed_at)
    live = replace(
        demo,
        provider="apify:clockworks~tiktok-scraper",
        raw_reference="apify://fixture/collision",
    )
    ingest(db, [live], observed_at)

    videos = db.scalars(select(Video).order_by(Video.id)).all()
    assert len(videos) == 2
    assert {video.provider for video in videos} == {
        "mock",
        "apify:clockworks~tiktok-scraper",
    }
    assert len({video.provider_id for video in videos}) == 2
    assert db.query(Creator).count() == 2
    snapshots = db.scalars(select(Snapshot)).all()
    assert {snapshot.source for snapshot in snapshots} == {
        "mock",
        "apify:clockworks~tiktok-scraper",
    }


def test_central_demo_fixture_exercises_every_lifecycle() -> None:
    db = database()
    now = cli.utc_now()
    for run_index in range(4):
        ingest(
            db,
            MockProvider(run_index).discover_videos(),
            now - timedelta(hours=18 - run_index * 6),
        )
    signals = build_or_update_toy_signals(db, now=now)
    assert len(signals) == 12
    assert {signal.lifecycle for signal in signals} == {
        "Insufficient evidence",
        "Emerging",
        "Accelerating",
        "Breakout",
        "Declining",
        "Saturated",
        "Viral",
    }
    assert {market for signal in signals for market in signal.markets} == {"GB", "PL"}
    assert db.query(ToySignal).count() == 12


def test_apify_cli_defaults_to_preflight_without_collecting(monkeypatch, capsys) -> None:
    provider = ApifyTikTokProvider(
        settings=ApifyProviderSettings(
            enabled=False,
            provider_mode="demo",
            default_market="GB",
            supported_markets=("GB", "PL"),
        ),
        search_queries=["STEM toys"],
    )
    called = False

    def unexpected_collect(_request):
        nonlocal called
        called = True
        raise AssertionError("A preflight-only CLI call started collection")

    monkeypatch.setattr(provider, "collect_sync", unexpected_collect)
    monkeypatch.setattr(cli, "_apify_provider", lambda _cfg=None: provider)
    monkeypatch.setattr(cli, "_month_spend", lambda: 0.0)
    cli.toy_discover([])
    output = capsys.readouterr().out
    assert '"executed": false' in output
    assert '"confirmation_required": true' in output
    assert not called
    assert not cli._confirmed([])
    assert cli._confirmed(["--confirm-live-run"])
    assert not cli._confirmed(["--confirm-live-run=yes"])


def test_apify_config_check_is_network_free() -> None:
    cfg = Settings(
        provider_type="apify",
        apify_enabled=False,
        toy_provider_mode="demo",
        apify_token="",
    )
    provider = cli._apify_provider(cfg)
    health = provider.health_check()
    assert not health["ok"]
    assert health["network_check"] == "not_run"
    assert health["token_configured"] is False


def test_cli_discovery_uses_central_taxonomy_unless_explicitly_overridden() -> None:
    taxonomy = load_toy_taxonomy()
    cfg = Settings(
        _env_file=None,
        provider_type="apify",
        apify_search_queries="",
        apify_hashtags="",
    )
    provider = cli._apify_provider(cfg)
    expected_queries = [
        term
        for language in sorted(taxonomy.search_terms)
        for term in taxonomy.search_terms[language]
    ]
    assert provider.search_queries == expected_queries
    assert provider.hashtags == list(taxonomy.hashtags)
    requests = cli._discovery_requests(provider)
    assert requests[0].source_values == tuple(expected_queries)
    assert requests[1].source_values == taxonomy.hashtags

    override = cli._apify_provider(
        Settings(
            _env_file=None,
            provider_type="apify",
            apify_search_queries="one deliberate query",
            apify_hashtags="one-deliberate-tag",
        )
    )
    assert override.search_queries == ["one deliberate query"]
    assert override.hashtags == ["one-deliberate-tag"]
