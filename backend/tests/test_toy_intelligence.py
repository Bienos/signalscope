from datetime import datetime, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.config import Settings
from app.domain.toys import classify_creator_type, classify_toy_content, load_toy_taxonomy
from app.models import (
    Creator,
    Opportunity,
    ProviderQuarantine,
    SignalDecision,
    SignalVideoEvidence,
    Snapshot,
    ToySignal,
    Video,
    ViralScore,
    Watchlist,
)
from app.services.toy_intelligence import (
    active_toy_signals,
    build_or_update_toy_signals,
    calculate_video_evidence,
    signal_evidence_identity,
)
from app.services.toy_api import provider_context, report_payload, serialize_signal


def db() -> Session:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return sessionmaker(engine)()


def add_video(
    session: Session,
    provider_id: str,
    creator_id: str,
    views: list[int | None],
    start: datetime,
    caption: str = "Sensory toy unboxing",
    hashtags: list[str] | None = None,
    provider: str = "synthetic",
) -> Video:
    creator = Creator(
        provider_id=creator_id,
        username=creator_id,
        display_name=None,
        region="GB",
        followers=None,
        niche="toy",
        apparent_minor=None,
        provider=provider,
    )
    session.add(creator)
    session.flush()
    video = Video(
        provider_id=provider_id,
        url=f"https://example.invalid/{provider_id}",
        creator_id=creator.id,
        sound_id=None,
        caption=caption,
        hashtags=hashtags or ["sensorytoys", "toyunboxing"],
        published_at=start - timedelta(hours=1),
        language="en",
        market="GB",
        category="toy",
        product_category=None,
        child_featured=None,
        safety_status="clear",
        provider=provider,
        raw_reference=f"synthetic://{provider_id}",
        missing_fields=[],
    )
    session.add(video)
    session.flush()
    for index, value in enumerate(views):
        observed_at = start + timedelta(hours=index * 6)
        session.add(
            Snapshot(
                video_id=video.id,
                collected_at=observed_at,
                freshness_at=observed_at,
                views=value,
                likes=None if value is None else max(1, value // 10),
                comments=None if value is None else max(1, value // 100),
                shares=None if value is None else max(1, value // 50),
                favourites=None if value is None else max(1, value // 40),
                missing_fields=["views"] if value is None else [],
                source=provider,
            )
        )
    session.commit()
    return video


def test_taxonomy_contains_exact_brief_seeds() -> None:
    taxonomy = load_toy_taxonomy()
    assert taxonomy.search_terms["en"][0] == "viral toys"
    assert taxonomy.search_terms["en"][-1] == "toys children keep playing with"
    assert taxonomy.search_terms["pl"][0] == "popularne zabawki"
    assert taxonomy.search_terms["pl"][-1] == "zabawki polecane przez rodziców"
    assert "montessoritoys" in taxonomy.hashtags
    assert taxonomy.product_categories == (
        "Sensory and fidget toys",
        "Plush and soft toys",
        "Blind boxes and collectibles",
        "Construction toys",
        "STEM and educational toys",
        "Arts and crafts",
        "Dolls and accessories",
        "Action figures",
        "Vehicles and remote-control toys",
        "Board games and puzzles",
        "Outdoor toys",
        "Pretend play",
        "Baby and toddler toys",
        "Screen-free toys",
        "Electronic and interactive toys",
        "Licensed character toys",
        "Retro and nostalgic toys",
        "Pocket-money toys",
        "Seasonal and gifting toys",
    )
    assert "Product test" in taxonomy.content_mechanisms
    assert "Unknown" in taxonomy.creator_types
    assert "Direct copying of identifiable children" in taxonomy.safety_flags


def test_classifier_is_deterministic_and_does_not_infer_a_child_creator() -> None:
    result = classify_toy_content(
        "Sensory toy unboxing with an explicit choking hazard",
        ["#sensorytoys", "#toyunboxing"],
    )
    assert result.toy_category == "Sensory and fidget toys"
    assert result.content_mechanism == "Unboxing"
    assert result.safety_flags == ("Choking risk",)
    assert classify_creator_type("A kid reviewing toys") == "Unknown"
    assert classify_toy_content("A popular short video", []).toy_category is None


def test_velocity_requires_two_and_acceleration_requires_three_observations() -> None:
    session = db()
    start = datetime(2026, 7, 13, 6)
    video = add_video(session, "one", "creator-one", [1_000], start)
    snapshots = session.scalars(
        select(Snapshot).where(Snapshot.video_id == video.id)
    ).all()
    calculated = calculate_video_evidence(video, snapshots)
    assert calculated.velocity is None
    assert calculated.acceleration is None
    assert "velocity_requires_two_view_observations" in calculated.missing_components

    add_video(session, "two", "creator-two", [1_000, 2_000], start)
    second_video = session.scalar(select(Video).where(Video.provider_id == "two"))
    second_snapshots = session.scalars(
        select(Snapshot).where(Snapshot.video_id == second_video.id)
    ).all()
    calculated = calculate_video_evidence(second_video, second_snapshots)
    assert calculated.velocity == 1_000 / 6
    assert calculated.acceleration is None

    add_video(session, "three", "creator-three", [1_000, 2_000, 5_000], start)
    third_video = session.scalar(select(Video).where(Video.provider_id == "three"))
    third_snapshots = session.scalars(
        select(Snapshot).where(Snapshot.video_id == third_video.id)
    ).all()
    calculated = calculate_video_evidence(third_video, third_snapshots)
    assert calculated.velocity == 3_000 / 6
    assert calculated.acceleration == (3_000 / 6) - (1_000 / 6)


def test_one_observation_is_insufficient_even_across_independent_creators() -> None:
    session = db()
    start = datetime(2026, 7, 13, 6)
    add_video(session, "one", "creator-one", [1_000], start)
    add_video(session, "two", "creator-two", [2_000], start)
    signals = build_or_update_toy_signals(session, now=start)
    assert len(signals) == 1
    signal = signals[0]
    assert signal.lifecycle == "Insufficient evidence"
    assert signal.recommended_decision == "Monitor"
    assert signal.unique_creators == 2
    assert signal.post_count == 2
    assert "velocity" in signal.missing_components
    assert session.query(SignalVideoEvidence).count() == 2


def test_signal_updates_are_explainable_idempotent_and_do_not_fabricate_baselines() -> None:
    session = db()
    start = datetime(2026, 7, 13, 6)
    add_video(session, "one", "creator-one", [1_000, 101_000, 401_000], start)
    add_video(session, "two", "creator-two", [2_000, 122_000, 482_000], start)
    now = start + timedelta(hours=12)
    first = build_or_update_toy_signals(session, now=now)
    second = build_or_update_toy_signals(session, now=now + timedelta(minutes=5))
    assert len(first) == len(second) == 1
    assert session.query(ToySignal).count() == 1
    assert session.query(SignalVideoEvidence).count() == 2
    signal = second[0]
    assert signal.lifecycle == "Accelerating"
    assert signal.recommended_decision == "Act"
    assert signal.confidence in {"Medium", "High"}
    assert 0 <= signal.opportunity_score <= 100
    assert signal.components["creator_baseline"] == {
        "status": "Unavailable unless observed",
        "value": None,
    }
    assert signal.components["coverage"] == "Configured monitored sample"
    confidence = signal.components["confidence"]
    assert confidence["market_consistency"] == 0.0
    assert confidence["market_evidence"]["status"] == "No cross-market confirmation"
    assert confidence["market_evidence"]["markets"] == ["GB"]
    assert "one collection market only" in confidence["market_evidence"]["explanation"]
    assert "not a virality prediction" in signal.explanation
    memberships = session.scalars(select(SignalVideoEvidence)).all()
    assert all(membership.metrics["acceleration_views_per_hour_squared"] is not None for membership in memberships)


def test_recurring_requires_persisted_prior_state_gap_and_reacceleration() -> None:
    session = db()
    start = datetime(2026, 7, 13, 6)
    videos = [
        add_video(session, "one", "creator-one", [1_000, 2_000, 5_000], start),
        add_video(session, "two", "creator-two", [2_000, 4_000, 10_000], start),
    ]
    first = build_or_update_toy_signals(session, now=start + timedelta(hours=12))[0]
    assert first.lifecycle == "Accelerating"
    assert first.components["lifecycle"]["recurrence"]["qualified"] is False
    assert (
        first.components["lifecycle"]["recurrence"]["reason"]
        == "No persisted prior signal assessment exists."
    )

    unchanged = build_or_update_toy_signals(
        session, now=start + timedelta(hours=90)
    )[0]
    assert unchanged.lifecycle != "Recurring"
    assert (
        unchanged.components["lifecycle"]["recurrence"]["reason"]
        == "No genuinely newer observation window exists."
    )

    for index, video in enumerate(videos):
        prior_views = 5_000 if index == 0 else 10_000
        for hour, views in ((84, prior_views + 1_000), (90, prior_views + 6_000), (96, prior_views + 21_000)):
            observed_at = start + timedelta(hours=hour)
            session.add(
                Snapshot(
                    video_id=video.id,
                    collected_at=observed_at,
                    freshness_at=observed_at,
                    views=views,
                    likes=max(1, views // 10),
                    comments=max(1, views // 100),
                    shares=max(1, views // 50),
                    favourites=max(1, views // 40),
                    missing_fields=[],
                    source="synthetic",
                )
            )
    session.commit()

    recurring = build_or_update_toy_signals(
        session, now=start + timedelta(hours=96)
    )[0]
    recurrence = recurring.components["lifecycle"]["recurrence"]
    assert recurring.lifecycle == "Recurring"
    assert recurrence["qualified"] is True
    assert recurrence["previous_lifecycle"] == "Accelerating"
    assert recurrence["observation_gap_hours"] == 84.0
    assert recurrence["reaccelerating"] is True

    idempotent = build_or_update_toy_signals(
        session, now=start + timedelta(hours=97)
    )[0]
    assert idempotent.lifecycle == "Recurring"
    assert idempotent.components["lifecycle"]["recurrence"]["qualified"] is True


def test_positive_reacceleration_inside_72_hours_is_not_recurring() -> None:
    session = db()
    start = datetime(2026, 7, 13, 6)
    videos = [
        add_video(session, "one", "creator-one", [1_000, 2_000, 5_000], start),
        add_video(session, "two", "creator-two", [2_000, 4_000, 10_000], start),
    ]
    initial = build_or_update_toy_signals(
        session, now=start + timedelta(hours=12)
    )[0]
    assert initial.lifecycle == "Accelerating"
    for index, video in enumerate(videos):
        prior_views = 5_000 if index == 0 else 10_000
        for hour, views in (
            (24, prior_views + 1_000),
            (30, prior_views + 6_000),
            (36, prior_views + 21_000),
        ):
            observed_at = start + timedelta(hours=hour)
            session.add(
                Snapshot(
                    video_id=video.id,
                    collected_at=observed_at,
                    freshness_at=observed_at,
                    views=views,
                    likes=max(1, views // 10),
                    comments=max(1, views // 100),
                    shares=max(1, views // 50),
                    favourites=max(1, views // 40),
                    source="synthetic",
                )
            )
    session.commit()
    assessed = build_or_update_toy_signals(
        session, now=start + timedelta(hours=36)
    )[0]
    recurrence = assessed.components["lifecycle"]["recurrence"]
    assert assessed.lifecycle == "Accelerating"
    assert recurrence["qualified"] is False
    assert recurrence["observation_gap_hours"] == 24.0
    assert "at least 72 hours is required" in recurrence["reason"]


def test_demo_and_live_evidence_are_isolated_and_never_relabelled(
    monkeypatch,
) -> None:
    from app.services import toy_api, toy_intelligence

    session = db()
    start = datetime(2026, 7, 13, 6)
    demo_cfg = Settings(
        _env_file=None,
        toy_provider_mode="demo",
        apify_enabled=False,
        apify_token="",
    )
    monkeypatch.setattr(toy_intelligence, "settings", lambda: demo_cfg)
    monkeypatch.setattr(toy_api, "settings", lambda: demo_cfg)
    add_video(session, "demo-one", "demo-creator", [1_000, 2_000], start)
    demo_signal = build_or_update_toy_signals(session, now=start)[0]
    assert signal_evidence_identity(session, demo_signal) == ("demo", ("synthetic",))

    live_cfg = Settings(
        _env_file=None,
        toy_provider_mode="live",
        apify_enabled=True,
        apify_token="test-token",
    )
    monkeypatch.setattr(toy_intelligence, "settings", lambda: live_cfg)
    monkeypatch.setattr(toy_api, "settings", lambda: live_cfg)

    # A configuration switch cannot turn existing synthetic rows into live data.
    assert build_or_update_toy_signals(session, now=start) == []
    fallback = provider_context(session)
    assert fallback["mode"] == "demo"
    assert fallback["mode_label"] == "DEMO TOY DATA"
    assert "only synthetic demo evidence" in fallback["provider"]["state"]
    assert serialize_signal(session, demo_signal)["demo"] is True

    add_video(
        session,
        "live-one",
        "live-creator",
        [2_000, 5_000],
        start,
        provider="apify:clockworks~tiktok-scraper",
    )
    live_signals = build_or_update_toy_signals(session, now=start)
    assert len(live_signals) == 1
    assert session.query(ToySignal).count() == 2
    assert active_toy_signals(session) == live_signals
    live_signal = live_signals[0]
    assert signal_evidence_identity(session, live_signal) == (
        "live",
        ("apify:clockworks~tiktok-scraper",),
    )
    assert serialize_signal(session, live_signal)["demo"] is False
    assert serialize_signal(session, demo_signal)["demo"] is True
    assert provider_context(session)["mode"] == "live"
    for signal in session.scalars(select(ToySignal)).all():
        providers = {
            session.get(Video, membership.video_id).provider
            for membership in session.scalars(
                select(SignalVideoEvidence).where(
                    SignalVideoEvidence.signal_id == signal.id
                )
            ).all()
        }
        assert len(providers) == 1


def test_report_opportunities_require_selection_or_include_flag() -> None:
    session = db()
    start = datetime(2026, 7, 13, 6)
    add_video(session, "one", "creator-one", [1_000], start)
    signal = build_or_update_toy_signals(session, now=start)[0]
    included = Opportunity(
        source_signal_id=signal.id,
        user_key="analyst",
        title="Included opportunity",
        include_in_report=True,
    )
    excluded = Opportunity(
        source_signal_id=signal.id,
        user_key="analyst",
        title="Excluded opportunity",
        include_in_report=False,
    )
    other_user = Opportunity(
        source_signal_id=signal.id,
        user_key="other-user",
        title="Other user's opportunity",
        include_in_report=True,
    )
    session.add_all([included, excluded, other_user])
    session.commit()
    default_payload = report_payload(session, user_key="analyst")
    assert [item["title"] for item in default_payload["creative_opportunities"]] == [
        "Included opportunity"
    ]
    selected_payload = report_payload(
        session,
        user_key="analyst",
        include_opportunity_ids=[excluded.id],
    )
    assert [item["title"] for item in selected_payload["creative_opportunities"]] == [
        "Excluded opportunity"
    ]
    empty_payload = report_payload(
        session,
        user_key="analyst",
        include_opportunity_ids=[],
    )
    assert empty_payload["creative_opportunities"] == []


def test_decision_opportunity_watchlist_and_quarantine_persist_without_fake_checks() -> None:
    session = db()
    start = datetime(2026, 7, 13, 6)
    add_video(session, "one", "creator-one", [1_000], start)
    signal = build_or_update_toy_signals(session, now=start)[0]
    session.add_all(
        [
            SignalDecision(
                signal_id=signal.id,
                decision="Monitor",
                reason="Needs another observation.",
                analyst_note="Review tomorrow.",
            ),
            Opportunity(
                source_signal_id=signal.id,
                title="Original sensory-toy test",
                decision="Monitor",
                originality_checks={},
                safety_checks={},
                evidence_limitations=["Only one observed snapshot per post"],
            ),
            Watchlist(
                name="Sensory and fidget toys",
                objective="Track evidence-backed category momentum.",
                categories=["Sensory and fidget toys"],
                markets=["GB"],
                languages=["en"],
            ),
            ProviderQuarantine(
                provider="synthetic",
                external_record_id="invalid-1",
                reason_code="missing_stable_id",
                redacted_summary="Required provider identifier was unavailable.",
                missing_fields=["provider_video_id"],
            ),
        ]
    )
    session.commit()
    opportunity = session.scalar(select(Opportunity))
    assert opportunity.source_signal_id == signal.id
    assert opportunity.originality_checks == {}
    assert opportunity.safety_checks == {}
    assert opportunity.include_in_report is False
    assert session.query(SignalDecision).count() == 1
    assert session.query(Watchlist).count() == 1
    assert session.query(ProviderQuarantine).count() == 1
    assert ViralScore.__table__.c.acceleration.nullable is True
