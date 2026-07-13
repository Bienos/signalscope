from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app import cli
from app.config import Settings
from app.db import Base
from app.models import Creator, Opportunity, Snapshot, Video
from app.providers.apify import ApifyProviderSettings, ApifyTikTokProvider
from app.services.toy_intelligence import build_or_update_toy_signals
from app.services.toy_monitoring import (
    MAX_DUE_REFRESH_URLS,
    plan_due_video_refreshes,
)

LIVE_PROVIDER = "apify:clockworks~tiktok-scraper"


def database() -> tuple[Session, sessionmaker[Session]]:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine)
    return factory(), factory


def add_live_video(
    db: Session,
    *,
    index: int,
    observed_at: datetime,
    availability: str = "available",
) -> Video:
    creator = Creator(
        provider_id=f"live-creator-{index}",
        username=f"live_creator_{index}",
        region="GB",
        niche="toy",
        provider=LIVE_PROVIDER,
    )
    db.add(creator)
    db.flush()
    video = Video(
        provider_id=f"live-video-{index}",
        url=(
            f"https://www.tiktok.com/@live_creator_{index}/video/"
            f"{7400000000000000000 + index}"
        ),
        creator_id=creator.id,
        caption="Sensory toy unboxing",
        hashtags=["sensorytoys", "toyunboxing"],
        published_at=observed_at - timedelta(hours=1),
        language="en",
        market="GB",
        collection_market="GB",
        category="toy",
        toy_category="Sensory and fidget toys",
        content_mechanism="Unboxing",
        safety_status="clear",
        availability_status=availability,
        provider=LIVE_PROVIDER,
        raw_reference=f"apify://fixture/{index}",
        first_observed_at=observed_at,
        last_observed_at=observed_at,
    )
    db.add(video)
    db.flush()
    db.add(
        Snapshot(
            video_id=video.id,
            collected_at=observed_at,
            freshness_at=observed_at,
            views=10_000 + index,
            likes=1_000,
            comments=100,
            shares=200,
            favourites=250,
            availability_state=availability,
            missing_fields=[],
            source=LIVE_PROVIDER,
        )
    )
    db.commit()
    return video


def seed_saved_signal(db: Session, *, count: int, start: datetime):
    videos = [
        add_live_video(db, index=index, observed_at=start) for index in range(count)
    ]
    signal = build_or_update_toy_signals(
        db, now=start, evidence_mode="live"
    )[0]
    db.add(
        Opportunity(
            source_signal_id=signal.id,
            state="saved",
            title="Saved toy signal",
            created_at=start,
            updated_at=start,
        )
    )
    db.commit()
    return signal, videos


def test_due_planner_is_read_only_live_only_and_strictly_capped() -> None:
    db, _factory = database()
    start = datetime(2026, 7, 1, 9)
    signal, videos = seed_saved_signal(db, count=3, start=start)

    plan = plan_due_video_refreshes(
        db, now=start + timedelta(hours=25), limit=2
    )
    assert plan.due_count == 3
    assert len(plan.selected) == 2
    assert plan.omitted_due_count == 1
    assert plan.applied_limit == 2
    assert all(item.signal_id == signal.id for item in plan.selected)
    assert all(item.saved for item in plan.selected)
    assert all(item.policy_offset_hours == 24 for item in plan.selected)
    assert {item.video_id for item in plan.selected} <= {video.id for video in videos}
    assert plan.payload()["read_only"] is True
    assert not db.dirty and not db.new and not db.deleted

    hard_capped = plan_due_video_refreshes(
        db, now=start + timedelta(hours=25), limit=MAX_DUE_REFRESH_URLS + 100
    )
    assert hard_capped.applied_limit == MAX_DUE_REFRESH_URLS

    demo_creator = Creator(
        provider_id="demo-extra-creator",
        username="demo_extra_creator",
        region="GB",
        niche="toy",
        provider="mock",
    )
    db.add(demo_creator)
    db.flush()
    demo_video = Video(
        provider_id="demo-extra-video",
        url="https://www.tiktok.com/@demo/video/7400000000000000999",
        creator_id=demo_creator.id,
        caption="Sensory toy unboxing",
        hashtags=["sensorytoys"],
        published_at=start,
        language="en",
        market="GB",
        category="toy",
        toy_category="Sensory and fidget toys",
        content_mechanism="Unboxing",
        provider="mock",
        raw_reference="mock://extra",
        first_observed_at=start,
        last_observed_at=start,
    )
    db.add(demo_video)
    db.flush()
    db.add(
        Snapshot(
            video_id=demo_video.id,
            collected_at=start,
            freshness_at=start,
            views=100,
            source="mock",
        )
    )
    db.commit()
    build_or_update_toy_signals(db, now=start, evidence_mode="demo")
    with_demo = plan_due_video_refreshes(
        db, now=start + timedelta(hours=25), limit=10
    )
    assert all("/@demo/" not in item.canonical_url for item in with_demo.selected)
    assert with_demo.skipped["demo_or_mixed_evidence"] >= 1


def test_terminal_state_gets_one_confirmation_then_stops() -> None:
    db, _factory = database()
    start = datetime(2026, 7, 1, 9)
    signal, videos = seed_saved_signal(db, count=1, start=start)
    video = videos[0]
    first = db.query(Snapshot).filter(Snapshot.video_id == video.id).one()
    first.availability_state = "private"
    video.availability_status = "private"
    db.commit()

    confirmation = plan_due_video_refreshes(
        db, now=start + timedelta(hours=25), limit=10
    )
    assert len(confirmation.selected) == 1
    item = confirmation.selected[0]
    assert item.signal_id == signal.id
    assert item.terminal_confirmation is True
    assert item.reason.startswith("Confirm the observed terminal state once")

    confirmed_at = start + timedelta(hours=25)
    db.add(
        Snapshot(
            video_id=video.id,
            collected_at=confirmed_at,
            freshness_at=confirmed_at,
            views=None,
            availability_state="private",
            missing_fields=["views"],
            source=LIVE_PROVIDER,
        )
    )
    db.commit()
    stopped = plan_due_video_refreshes(
        db, now=confirmed_at + timedelta(hours=25), limit=10
    )
    assert stopped.selected == ()
    assert stopped.skipped["terminal_confirmed"] == 1


def test_due_cli_prints_plan_and_preflight_without_starting_provider(
    monkeypatch, capsys
) -> None:
    db, factory = database()
    start = datetime(2026, 7, 1, 9)
    seed_saved_signal(db, count=3, start=start)
    db.close()
    provider = ApifyTikTokProvider(
        settings=ApifyProviderSettings(
            enabled=False,
            provider_mode="demo",
            default_market="GB",
            supported_markets=("GB", "PL"),
        )
    )
    collected = False

    def unexpected_collect(_request):
        nonlocal collected
        collected = True
        raise AssertionError("Preflight-only due planning started a provider run")

    monkeypatch.setattr(provider, "collect_sync", unexpected_collect)
    monkeypatch.setattr(cli, "SessionLocal", factory)
    monkeypatch.setattr(cli, "_apify_provider", lambda _cfg=None: provider)
    monkeypatch.setattr(cli, "_month_spend", lambda: 0.0)
    monkeypatch.setattr(
        cli,
        "settings",
        lambda: Settings(_env_file=None, apify_enabled=False, toy_provider_mode="demo"),
    )
    original_planner = cli.plan_due_video_refreshes
    monkeypatch.setattr(
        cli,
        "plan_due_video_refreshes",
        lambda session, limit: original_planner(
            session, now=start + timedelta(hours=25), limit=limit
        ),
    )

    cli.toy_refresh(["--due", "--limit", "2"])
    output = capsys.readouterr().out
    assert '"executed": false' in output
    assert '"selected_count": 2' in output
    assert '"read_only": true' in output
    assert '"confirmation_flag": "--confirm-live-run"' in output
    assert '"preflights"' in output
    assert not collected
