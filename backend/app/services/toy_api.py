from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
from statistics import median
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    Creator,
    DailyReport,
    Opportunity,
    ProviderRun,
    SignalDecision,
    SignalVideoEvidence,
    Snapshot,
    Sound,
    ToySignal,
    Video,
    Watchlist,
)
from app.services.toy_intelligence import (
    active_toy_signals,
    active_videos,
    configured_evidence_mode,
    evidence_mode_for_provider,
    selected_evidence_mode,
    signal_evidence_identity,
)

MONITORED_SAMPLE_WARNING = (
    "Configured monitored sample only; coverage is not exhaustive and SignalScope is "
    "not affiliated with TikTok or ByteDance."
)


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def freshness_status(value: datetime | None, *, now: datetime | None = None) -> str:
    if value is None:
        return "Unavailable"
    current = now or utc_now()
    age_hours = max(0.0, (current - value).total_seconds() / 3600)
    return "Fresh" if age_hours <= settings().expected_freshness_hours else "Stale"


def provider_context(db: Session) -> dict[str, Any]:
    cfg = settings()
    configured_mode = configured_evidence_mode()
    mode = selected_evidence_mode(db)
    videos = active_videos(db, mode=mode)
    video_ids = [video.id for video in videos]
    providers = sorted({video.provider for video in videos})
    provider_name = (
        "MockProvider"
        if mode == "demo"
        else ", ".join(providers)
        if providers
        else "Unavailable"
    )
    run_query = select(ProviderRun)
    if providers:
        run_query = run_query.where(ProviderRun.provider.in_(providers))
    else:
        run_query = run_query.where(ProviderRun.id == -1)
    latest_run = db.scalar(run_query.order_by(ProviderRun.started_at.desc()))
    latest_observation = (
        db.scalar(
            select(func.max(Snapshot.freshness_at))
            .join(Video, Video.id == Snapshot.video_id)
            .where(
                Snapshot.video_id.in_(video_ids),
                Snapshot.source == Video.provider,
            )
        )
        if video_ids
        else None
    )
    successful_run = db.scalar(
        run_query.where(
            ProviderRun.status.in_(["success", "succeeded", "completed", "ready"])
        ).order_by(ProviderRun.finished_at.desc(), ProviderRun.started_at.desc())
    )
    live_collection_enabled = (
        cfg.apify_enabled and bool(cfg.apify_token.get_secret_value())
    )
    if mode == "unavailable":
        state = (
            "Demo mode configured; stored live evidence is hidden"
            if configured_mode == "demo"
            else "No provider evidence is available"
        )
    elif configured_mode == "live" and mode == "demo":
        state = "Live mode configured; only synthetic demo evidence is available"
    elif latest_run is None:
        state = "Synthetic demo evidence" if mode == "demo" else "Stored provider evidence"
    else:
        state = latest_run.status
    quality_status = "Unavailable"
    if latest_run:
        rate = latest_run.missing_field_rate
        quality_status = (
            "Partial dataset"
            if latest_run.status.casefold() not in {"success", "succeeded", "completed", "ready"}
            or (rate is not None and rate > 0.25)
            else "Quality checks passed"
        )
    elif mode == "demo":
        quality_status = "Synthetic fixtures"
    return {
        "mode": mode,
        "mode_label": "LIVE PROVIDER DATA" if mode == "live" else "DEMO TOY DATA" if mode == "demo" else "PROVIDER UNAVAILABLE",
        "coverage": MONITORED_SAMPLE_WARNING,
        "provider": {
            "name": provider_name,
            "provider_ids": providers,
            "state": state,
            "configured_mode": configured_mode,
            "collection_enabled": live_collection_enabled,
            "last_success": _iso(successful_run.finished_at or successful_run.started_at)
            if successful_run
            else None,
            "last_observation": _iso(latest_observation),
            "freshness_status": freshness_status(latest_observation),
            "quality_status": quality_status,
        },
    }


def collection_envelope(db: Session, items: list[dict[str, Any]]) -> dict[str, Any]:
    context = provider_context(db)
    visible_items = [
        item
        for item in items
        if "evidence_mode" not in item
        or item["evidence_mode"] == context["mode"]
    ]
    return {
        "items": visible_items,
        "total": len(visible_items),
        "mode": context["mode"],
        "mode_label": context["mode_label"],
        "coverage": context["coverage"],
        "provider": context["provider"]["name"],
        "last_observation": context["provider"]["last_observation"],
    }


def serialize_signal(
    db: Session,
    signal: ToySignal,
    *,
    user_key: str = "single-user",
    include_detail: bool = False,
) -> dict[str, Any]:
    memberships = list(
        db.scalars(
            select(SignalVideoEvidence).where(SignalVideoEvidence.signal_id == signal.id)
        ).all()
    )
    metrics = [membership.metrics or {} for membership in memberships]
    snapshot_count = sum(int(value.get("snapshot_count") or 0) for value in metrics)
    velocity = _median_nullable(
        [value.get("velocity_views_per_hour") for value in metrics]
    )
    acceleration = _median_nullable(
        [value.get("acceleration_views_per_hour_squared") for value in metrics]
    )
    decision = db.scalar(
        select(SignalDecision).where(
            SignalDecision.signal_id == signal.id,
            SignalDecision.user_key == user_key,
        )
    )
    opportunity = db.scalar(
        select(Opportunity)
        .where(
            Opportunity.source_signal_id == signal.id,
            Opportunity.user_key == user_key,
        )
        .order_by(Opportunity.updated_at.desc())
    )
    evidence_mode, evidence_providers = signal_evidence_identity(db, signal)
    safety_state = _safety_label(signal.safety_state)
    result: dict[str, Any] = {
        "id": str(signal.id),
        "title": signal.title,
        "conclusion": signal.explanation,
        "category": signal.toy_category,
        "mechanism": signal.content_mechanism,
        "lifecycle": signal.lifecycle,
        "recommendation": decision.decision if decision else signal.recommended_decision,
        "markets": list(signal.markets or []),
        "languages": list(signal.languages or []),
        "opportunity_score": _number(signal.opportunity_score),
        "confidence": signal.confidence,
        "confidence_score": _number(signal.confidence_score),
        "freshness_at": _iso(signal.data_freshness_at),
        "freshness_status": freshness_status(signal.data_freshness_at),
        "saturation": _number(signal.saturation_score),
        "velocity": velocity,
        "acceleration": acceleration,
        "creator_spread": signal.unique_creators,
        "post_count": signal.post_count,
        "snapshot_count": snapshot_count,
        "why_it_matters": signal.main_supporting_evidence,
        "main_limitation": signal.main_contradictory_evidence,
        "decision_window": _decision_window(signal.lifecycle),
        "safety_state": safety_state,
        "score_version": signal.score_version,
        "demo": evidence_mode == "demo",
        "evidence_mode": evidence_mode,
        "evidence_provider": ", ".join(evidence_providers) or "Unavailable",
        "decision": (
            {
                "recommendation": decision.decision,
                "reason": decision.reason,
                "review_date": _iso(decision.review_date),
            }
            if decision
            else None
        ),
        "opportunity": serialize_opportunity(db, opportunity) if opportunity else None,
    }
    if include_detail:
        detail = _signal_detail(db, signal, memberships)
        result.update(detail)
    return result


def _signal_detail(
    db: Session,
    signal: ToySignal,
    memberships: list[SignalVideoEvidence],
) -> dict[str, Any]:
    evidence: list[dict[str, Any]] = []
    creator_types: set[str] = set()
    safety_flags: set[str] = set()
    missing_fields: set[str] = set(signal.missing_components or [])
    providers: set[str] = set()
    first_observed: datetime | None = None
    last_observed: datetime | None = None
    for membership in memberships:
        video = db.get(Video, membership.video_id)
        if video is None:
            continue
        creator = db.get(Creator, video.creator_id)
        sound = db.get(Sound, video.sound_id) if video.sound_id else None
        snapshots = db.scalars(
            select(Snapshot)
            .where(
                Snapshot.video_id == video.id,
                Snapshot.source == video.provider,
            )
            .order_by(Snapshot.collected_at)
        ).all()
        latest = snapshots[-1] if snapshots else None
        previous = snapshots[-2] if len(snapshots) >= 2 else None
        growth = (
            latest.views - previous.views
            if latest and previous and latest.views is not None and previous.views is not None
            else None
        )
        creator_types.add(creator.creator_type if creator else "Unknown")
        safety_flags.update(video.safety_flags or [])
        missing_fields.update(video.missing_fields or [])
        if latest:
            missing_fields.update(latest.missing_fields or [])
            first_observed = min(first_observed, snapshots[0].collected_at) if first_observed else snapshots[0].collected_at
            last_observed = max(last_observed, latest.collected_at) if last_observed else latest.collected_at
        providers.add(video.provider)
        evidence.append(
            {
                "id": str(video.id),
                "caption": video.caption,
                "creator": creator.username if creator else "Unavailable",
                "creator_type": creator.creator_type if creator else "Unknown",
                "published_at": _iso(video.published_at),
                "canonical_url": video.url,
                "views": latest.views if latest else None,
                "growth": growth,
                "velocity": (membership.metrics or {}).get("velocity_views_per_hour"),
                "hashtags": list(video.hashtags or []),
                "sound": sound.title if sound else None,
                "market": video.collection_market or video.market,
                "evidence_type": membership.evidence_type,
                "missing_fields": sorted(
                    set(video.missing_fields or []).union(latest.missing_fields or [] if latest else [])
                ),
            }
        )
    confidence_components = (signal.components or {}).get("confidence", {})
    market_evidence = confidence_components.get("market_evidence", {})
    market_confidence_note = market_evidence.get(
        "status", "Cross-market evidence unavailable"
    )
    return {
        "evidence": evidence,
        "relationships": {
            "hashtags": list(signal.related_hashtags or []),
            "sounds": list(signal.related_sounds or []),
            "creator_types": sorted(creator_types),
            "market_notes": [
                f"{market} is collection context, not audience geography."
                for market in signal.markets or []
            ],
        },
        "quality": {
            "snapshot_count": sum(int((membership.metrics or {}).get("snapshot_count") or 0) for membership in memberships),
            "first_observed": _iso(first_observed),
            "last_observed": _iso(last_observed),
            "missing_fields": sorted(missing_fields),
            "coverage_limitations": [MONITORED_SAMPLE_WARNING, "One observation is not a trend; acceleration needs three view observations."],
            "provider": ", ".join(sorted(providers)) or "Unavailable",
            "cohort_size": signal.cohort_size,
            "confidence_explanation": (
                f"{signal.confidence} confidence ({signal.confidence_score:.0f}/100) based on "
                f"snapshot adequacy, {signal.unique_creators} independent creators, completeness, "
                f"freshness, cohort size and provider health. {market_confidence_note}."
            ),
            "confidence_components": confidence_components,
        },
        "risks": {
            "safety": sorted(safety_flags) or ["No automated safety concern observed; human review remains required."],
            "copyright": ["Adapt the broad mechanism, not a protected execution or identifiable creator."],
            "product_claims": ["Verify educational and developmental claims before publication."],
            "music_rights": "Unknown",
            "child_privacy": ["No creator age, child identity or audience age is inferred."],
            "evidence_limitations": [signal.main_contradictory_evidence, MONITORED_SAMPLE_WARNING],
        },
    }


def serialize_opportunity(db: Session, item: Opportunity) -> dict[str, Any]:
    signal = db.get(ToySignal, item.source_signal_id)
    evidence_mode, evidence_providers = (
        signal_evidence_identity(db, signal) if signal else ("unavailable", ())
    )
    return {
        "id": str(item.id),
        "signal_id": str(item.source_signal_id),
        "signal_title": signal.title if signal else "Unavailable source signal",
        "recommendation": item.decision,
        "title": item.title,
        "toy_category": signal.toy_category if signal else "Unavailable",
        "content_mechanism": item.mechanism or (signal.content_mechanism if signal else "Unavailable"),
        "why_it_is_moving": item.rationale or (signal.main_supporting_evidence if signal else "Unavailable"),
        "audience_need": item.audience_need,
        "original_hook": item.original_hook,
        "content_structure": _as_list(item.content_structure),
        "creator_type": item.recommended_creator_type,
        "production_complexity": item.production_complexity,
        "decision_window": item.decision_window,
        "elements_not_to_copy": list(item.elements_not_to_copy or []),
        "safety_considerations": list(item.safety_considerations or []),
        "rights_considerations": list(item.rights_considerations or []),
        "evidence_limitations": list(item.evidence_limitations or []),
        "review_status": item.review_status,
        "include_in_report": item.include_in_report,
        "evidence_mode": evidence_mode,
        "evidence_provider": ", ".join(evidence_providers) or "Unavailable",
    }


def creator_collection(db: Session) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    signals = active_toy_signals(db)
    selected_video_ids = {video.id for video in active_videos(db)}
    for creator in db.scalars(select(Creator).where(Creator.removed.is_(False))).all():
        videos = db.scalars(select(Video).where(Video.creator_id == creator.id, Video.removed.is_(False))).all()
        toy_videos = [
            video
            for video in videos
            if video.toy_category and video.id in selected_video_ids
        ]
        if not toy_videos:
            continue
        calculated_velocities: list[float] = []
        freshness_values: list[datetime] = []
        for video in toy_videos:
            snapshots = db.scalars(
                select(Snapshot)
                .where(
                    Snapshot.video_id == video.id,
                    Snapshot.source == video.provider,
                )
                .order_by(Snapshot.collected_at)
            ).all()
            if snapshots:
                freshness_values.append(snapshots[-1].freshness_at)
            if len(snapshots) >= 2 and snapshots[-1].views is not None and snapshots[-2].views is not None:
                hours = (snapshots[-1].collected_at - snapshots[-2].collected_at).total_seconds() / 3600
                if hours > 0:
                    calculated_velocities.append((snapshots[-1].views - snapshots[-2].views) / hours)
        matched = [
            signal
            for signal in signals
            if signal.toy_category in {video.toy_category for video in toy_videos}
            and signal.markets and signal.markets[0] in {video.market for video in toy_videos}
        ]
        breakout = next((signal.title for signal in matched if signal.lifecycle in {"Breakout", "Accelerating"}), None)
        rows.append(
            {
                "id": str(creator.id),
                "username": creator.username,
                "display_name": creator.display_name or creator.username,
                "creator_type": creator.creator_type or "Unknown",
                "toy_categories": sorted({video.toy_category for video in toy_videos if video.toy_category}),
                "followers": creator.followers,
                "recent_post_count": len(toy_videos),
                "baseline_velocity": round(median(calculated_velocities), 2) if len(calculated_velocities) >= 3 else None,
                "breakout_signal": breakout,
                "market": toy_videos[0].collection_market or toy_videos[0].market,
                "evidence_quality": "High" if len(calculated_velocities) >= 3 else "Medium" if calculated_velocities else "Low",
                "freshness_at": _iso(max(freshness_values) if freshness_values else creator.last_observed_at),
                "evidence_mode": evidence_mode_for_provider(toy_videos[0].provider),
                "provider": toy_videos[0].provider,
            }
        )
    return rows


def hashtag_collection(db: Session) -> list[dict[str, Any]]:
    aggregates: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(
        lambda: {"posts": set(), "creators": set(), "categories": set(), "mechanisms": set(), "related": Counter(), "freshness": []}
    )
    toy_videos = [video for video in active_videos(db) if video.toy_category is not None]
    for video in toy_videos:
        market = video.collection_market or video.market
        tags = [str(tag).removeprefix("#") for tag in video.hashtags or []]
        for tag in tags:
            record = aggregates[(video.provider, tag, market)]
            record["posts"].add(video.id)
            record["creators"].add(video.creator_id)
            record["categories"].add(video.toy_category)
            record["mechanisms"].add(video.content_mechanism or "Unknown")
            record["related"].update(other for other in tags if other != tag)
            latest = db.scalar(
                select(Snapshot.freshness_at)
                .where(
                    Snapshot.video_id == video.id,
                    Snapshot.source == video.provider,
                )
                .order_by(Snapshot.collected_at.desc())
            )
            if latest:
                record["freshness"].append(latest)
    rows = []
    for (provider, name, market), record in sorted(
        aggregates.items(), key=lambda item: -len(item[1]["posts"])
    ):
        creators = len(record["creators"])
        posts = len(record["posts"])
        rows.append({
            "id": f"{market}:{name}",
            "name": f"#{name}",
            "observed_posts": posts,
            "unique_creators": creators,
            "creator_growth": None,
            "related_hashtags": [f"#{tag}" for tag, _ in record["related"].most_common(5)],
            "categories": sorted(record["categories"]),
            "mechanisms": sorted(record["mechanisms"]),
            "lifecycle": "Insufficient evidence" if posts < 2 or creators < 2 else "Emerging",
            "saturation": min(100.0, round(creators / max(posts, 1) * 50 + posts * 2, 1)),
            "market": market,
            "freshness_at": _iso(max(record["freshness"]) if record["freshness"] else None),
            "evidence_mode": evidence_mode_for_provider(provider),
            "provider": provider,
        })
    return rows


def sound_collection(db: Session) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    selected_video_ids = {video.id for video in active_videos(db)}
    for sound in db.scalars(select(Sound)).all():
        videos = db.scalars(select(Video).where(Video.sound_id == sound.id, Video.toy_category.is_not(None), Video.removed.is_(False))).all()
        videos = [video for video in videos if video.id in selected_video_ids]
        if not videos:
            continue
        velocities: list[float] = []
        freshness: list[datetime] = []
        for video in videos:
            snapshots = db.scalars(
                select(Snapshot)
                .where(
                    Snapshot.video_id == video.id,
                    Snapshot.source == video.provider,
                )
                .order_by(Snapshot.collected_at)
            ).all()
            if snapshots:
                freshness.append(snapshots[-1].freshness_at)
            if len(snapshots) >= 2 and snapshots[-1].views is not None and snapshots[-2].views is not None:
                hours = (snapshots[-1].collected_at - snapshots[-2].collected_at).total_seconds() / 3600
                if hours > 0:
                    velocities.append((snapshots[-1].views - snapshots[-2].views) / hours)
        creators = len({video.creator_id for video in videos})
        lifecycle = "Insufficient evidence" if creators < 2 or len(velocities) < 2 else "Emerging"
        rows.append({
            "id": str(sound.id),
            "title": sound.title,
            "toy_post_adoption": len(videos),
            "independent_creators": creators,
            "categories": sorted({video.toy_category for video in videos if video.toy_category}),
            "post_momentum": round(median(velocities), 2) if velocities else None,
            "lifecycle": lifecycle,
            "freshness_at": _iso(max(freshness) if freshness else sound.last_observed_at),
            "rights_status": "Unknown",
            "evidence_mode": evidence_mode_for_provider(videos[0].provider),
            "provider": videos[0].provider,
        })
    return rows


def watchlist_collection(db: Session) -> list[dict[str, Any]]:
    signals = active_toy_signals(db)
    rows = []
    for item in db.scalars(select(Watchlist).where(Watchlist.enabled.is_(True))).all():
        matching = [signal for signal in signals if signal.toy_category in set(item.categories or [])]
        latest = max((signal.last_calculated_at for signal in matching), default=None)
        rows.append({
            "id": str(item.id),
            "name": item.name,
            "objective": item.objective,
            "categories": list(item.categories or []),
            "markets": list(item.markets or []),
            "languages": list(item.languages or []),
            "last_important_change": _iso(latest) or "Insufficient history",
            "signals_requiring_attention": sum(signal.recommended_decision == "Act" for signal in matching),
            "last_reviewed": _iso(item.last_reviewed_at),
            "data_status": freshness_status(latest),
        })
    return rows


def _decision_window(lifecycle: str) -> str:
    return {
        "Breakout": "Decide within 24 hours",
        "Accelerating": "Review within 24 hours",
        "Emerging": "Review after the next observation",
        "Viral": "Validate saturation before acting",
        "Saturated": "Hold unless an original angle is available",
        "Declining": "Do not prioritise without new evidence",
    }.get(lifecycle, "Wait for additional observations")


def _safety_label(value: str) -> str:
    normalised = value.casefold()
    if "review" in normalised:
        return "Review"
    if normalised == "clear":
        return "Clear"
    return "Hold"


def _median_nullable(values: list[Any]) -> float | None:
    observed = [float(value) for value in values if isinstance(value, (int, float))]
    return round(median(observed), 2) if observed else None


def _number(value: Any) -> float | None:
    return round(float(value), 2) if isinstance(value, (int, float)) else None


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _as_list(value: str | list[str] | None) -> list[str]:
    if isinstance(value, list):
        return value
    if not value:
        return []
    return [line.strip(" -") for line in value.splitlines() if line.strip(" -")]


def report_payload(
    db: Session,
    *,
    user_key: str = "single-user",
    include_opportunity_ids: list[int] | None = None,
) -> dict[str, Any]:
    signals = [
        serialize_signal(db, signal, user_key=user_key)
        for signal in active_toy_signals(db)
    ]
    opportunity_query = select(Opportunity).where(Opportunity.user_key == user_key)
    if include_opportunity_ids is None:
        opportunity_query = opportunity_query.where(
            Opportunity.include_in_report.is_(True)
        )
    else:
        opportunity_query = opportunity_query.where(
            Opportunity.id.in_(include_opportunity_ids)
        )
    opportunities = [
        serialize_opportunity(db, item)
        for item in db.scalars(
            opportunity_query.order_by(Opportunity.updated_at.desc())
        ).all()
    ]
    current_mode = provider_context(db)["mode"]
    opportunities = [
        item for item in opportunities if item["evidence_mode"] == current_mode
    ]
    act = [signal for signal in signals if signal["recommendation"] == "Act"]
    monitor = [signal for signal in signals if signal["recommendation"] == "Monitor"]
    avoid = [signal for signal in signals if signal["recommendation"] == "Avoid"]
    return {
        "schema_version": "toy-report-1.0",
        "executive_summary": (
            f"{len(act)} signals require action, {len(monitor)} need more evidence and "
            f"{len(avoid)} should be held or avoided within the configured toy-market sample."
        ),
        "act": act,
        "monitor": monitor,
        "avoid": avoid,
        "emerging_categories": sorted({signal["category"] for signal in act + monitor}),
        "emerging_creators": creator_collection(db)[:10],
        "emerging_hashtags": hashtag_collection(db)[:15],
        "content_mechanisms": sorted({signal["mechanism"] for signal in act + monitor}),
        "creative_opportunities": opportunities,
        "safety_and_originality": [
            "Use the mechanism, not protected expression or an identifiable creator's execution.",
            "Complete toy-safety, product-claim, music-rights and child-privacy review before use.",
        ],
        "evidence_and_limitations": [
            MONITORED_SAMPLE_WARNING,
            "Apify is not an official TikTok API.",
            "One observation is not a trend; acceleration requires at least three view observations.",
            "Creator account region is not audience geography; music rights remain unknown.",
        ],
        "methodology": (
            "Signals cluster observed toy posts by product category, content mechanism, market and "
            "language. Lifecycle, opportunity and confidence remain separate, versioned assessments."
        ),
        "metadata": {
            "generated_at": _iso(utc_now()),
            "mode": provider_context(db)["mode"],
            "coverage": MONITORED_SAMPLE_WARNING,
            "score_version": "toy-1.0",
        },
    }


def serialize_report(db: Session, report: DailyReport) -> dict[str, Any]:
    payload = report.payload or {}
    if payload.get("schema_version") != "toy-report-1.0":
        return {
            "id": report.id,
            "date": report.report_date,
            "status": "Legacy report",
            "executive_summary": "This report predates the toy decision workflow.",
            "act": [],
            "monitor": [],
            "avoid": [],
            "opportunities": [],
            "limitations": [MONITORED_SAMPLE_WARNING],
            "methodology": "Legacy report; regenerate to use the toy-market methodology.",
            "evidence_mode": "unavailable",
        }
    return {
        "id": report.id,
        "date": report.report_date,
        "status": report.status,
        "executive_summary": payload.get("executive_summary", ""),
        "act": payload.get("act", []),
        "monitor": payload.get("monitor", []),
        "avoid": payload.get("avoid", []),
        "opportunities": payload.get("creative_opportunities", []),
        "limitations": payload.get("evidence_and_limitations", []),
        "methodology": payload.get("methodology", ""),
        "evidence_mode": payload.get("metadata", {}).get("mode", "unavailable"),
    }
