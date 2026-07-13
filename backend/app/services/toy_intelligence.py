from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from math import log1p
from statistics import median
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.domain.toys import classify_toy_content
from app.models import (
    ProviderRun,
    SignalVideoEvidence,
    Snapshot,
    Sound,
    ToySignal,
    Video,
)

SCORE_VERSION = "toy-1.0"
UNKNOWN_MECHANISM = "Unknown"
DEMO_PROVIDERS = frozenset({"mock", "synthetic"})
RECURRING_OBSERVATION_GAP_HOURS = 72.0
RECURRING_PRIOR_LIFECYCLES = frozenset(
    {"Emerging", "Accelerating", "Breakout", "Viral", "Recurring"}
)


@dataclass(frozen=True)
class CalculatedVideoEvidence:
    video: Video
    snapshot_count: int
    view_snapshot_count: int
    latest_views: int | None
    velocity: float | None
    acceleration: float | None
    share_save_rate: float | None
    completeness: float
    freshness_at: datetime | None
    first_observed_at: datetime | None
    missing_components: tuple[str, ...]

    def metrics(self) -> dict:
        return {
            "snapshot_count": self.snapshot_count,
            "view_snapshot_count": self.view_snapshot_count,
            "latest_views": self.latest_views,
            "velocity_views_per_hour": _rounded(self.velocity),
            "acceleration_views_per_hour_squared": _rounded(self.acceleration),
            "share_save_rate": _rounded(self.share_save_rate, 6),
            "latest_metric_completeness": round(self.completeness, 3),
            "freshness_at": self.freshness_at.isoformat() if self.freshness_at else None,
            "first_observed_at": (
                self.first_observed_at.isoformat() if self.first_observed_at else None
            ),
            "missing_components": list(self.missing_components),
        }


def _rounded(value: float | None, digits: int = 2) -> float | None:
    return round(value, digits) if value is not None else None


def _utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def calculate_video_evidence(
    video: Video,
    snapshots: Sequence[Snapshot],
) -> CalculatedVideoEvidence:
    """Calculate only what the observations support.

    Velocity needs two observed view values. Acceleration needs three. Missing
    provider metrics are never converted to zero and creator baselines are not
    manufactured.
    """

    ordered = sorted(snapshots, key=lambda snapshot: _utc_naive(snapshot.collected_at))
    view_observations = [snapshot for snapshot in ordered if snapshot.views is not None]
    missing: list[str] = []
    velocity: float | None = None
    acceleration: float | None = None

    if len(view_observations) >= 2:
        previous, current = view_observations[-2:]
        elapsed_hours = (
            _utc_naive(current.collected_at) - _utc_naive(previous.collected_at)
        ).total_seconds() / 3600
        if elapsed_hours > 0:
            velocity = (current.views - previous.views) / elapsed_hours  # type: ignore[operator]
        else:
            missing.append("velocity_non_positive_interval")
    else:
        missing.append("velocity_requires_two_view_observations")

    if len(view_observations) >= 3:
        first, previous, current = view_observations[-3:]
        first_hours = (
            _utc_naive(previous.collected_at) - _utc_naive(first.collected_at)
        ).total_seconds() / 3600
        second_hours = (
            _utc_naive(current.collected_at) - _utc_naive(previous.collected_at)
        ).total_seconds() / 3600
        if first_hours > 0 and second_hours > 0:
            first_velocity = (previous.views - first.views) / first_hours  # type: ignore[operator]
            second_velocity = (current.views - previous.views) / second_hours  # type: ignore[operator]
            acceleration = second_velocity - first_velocity
        else:
            missing.append("acceleration_non_positive_interval")
    else:
        missing.append("acceleration_requires_three_view_observations")

    latest = ordered[-1] if ordered else None
    required_metrics = ("views", "likes", "comments", "shares", "favourites")
    completeness = (
        sum(getattr(latest, field) is not None for field in required_metrics)
        / len(required_metrics)
        if latest
        else 0.0
    )
    share_save_rate: float | None = None
    if (
        latest
        and latest.views is not None
        and latest.views > 0
        and latest.shares is not None
        and latest.favourites is not None
    ):
        share_save_rate = (latest.shares + latest.favourites) / latest.views
    else:
        missing.append("share_save_rate_unavailable")

    return CalculatedVideoEvidence(
        video=video,
        snapshot_count=len(ordered),
        view_snapshot_count=len(view_observations),
        latest_views=view_observations[-1].views if view_observations else None,
        velocity=velocity,
        acceleration=acceleration,
        share_save_rate=share_save_rate,
        completeness=completeness,
        freshness_at=(latest.freshness_at if latest else None),
        first_observed_at=(ordered[0].collected_at if ordered else None),
        missing_components=tuple(dict.fromkeys(missing)),
    )


def _legacy_toy_category(value: str | None) -> str | None:
    if not value:
        return None
    aliases = {
        "Educational & STEM toys": "STEM and educational toys",
        "Sensory toys": "Sensory and fidget toys",
        "Collectibles": "Blind boxes and collectibles",
        "Construction toys": "Construction toys",
        "Plush toys": "Plush and soft toys",
        "Dolls & action figures": "Dolls and accessories",
        "Outdoor toys": "Outdoor toys",
        "Parent & gift-buyer content": "Seasonal and gifting toys",
    }
    return aliases.get(value)


def evidence_mode_for_provider(provider: str) -> str:
    """Classify persisted evidence without relying on the current configuration.

    A configuration switch must never turn a synthetic observation into live
    evidence. Mock/synthetic sources are therefore permanently demo evidence;
    every other persisted provider is non-demo provider evidence.
    """

    normalized = provider.strip().casefold()
    return "demo" if normalized in DEMO_PROVIDERS or normalized.startswith("mock:") else "live"


def configured_evidence_mode() -> str:
    configured = settings().toy_provider_mode.strip().casefold()
    return configured if configured in {"demo", "live"} else "unavailable"


def available_evidence_modes(db: Session) -> set[str]:
    providers = db.scalars(
        select(Video.provider).where(Video.removed.is_(False)).distinct()
    ).all()
    return {evidence_mode_for_provider(provider) for provider in providers if provider}


def selected_evidence_mode(db: Session) -> str:
    """Return the evidence mode that may be displayed for the current config.

    Live mode falls back to an explicitly labelled demo only when no live
    evidence exists. Demo mode never exposes stored live evidence.
    """

    configured = configured_evidence_mode()
    available = available_evidence_modes(db)
    if configured == "live":
        if "live" in available:
            return "live"
        if "demo" in available:
            return "demo"
    elif configured == "demo" and "demo" in available:
        return "demo"
    return "unavailable"


def active_videos(db: Session, *, mode: str | None = None) -> list[Video]:
    selected = mode or selected_evidence_mode(db)
    if selected not in {"demo", "live"}:
        return []
    return [
        video
        for video in db.scalars(select(Video).where(Video.removed.is_(False))).all()
        if evidence_mode_for_provider(video.provider) == selected
    ]


def signal_evidence_identity(db: Session, signal: ToySignal) -> tuple[str, tuple[str, ...]]:
    components = signal.components or {}
    stored_mode = components.get("evidence_mode")
    stored_providers = tuple(
        sorted(str(value) for value in components.get("evidence_providers", []) if value)
    )
    providers = tuple(
        sorted(
            {
                provider
                for provider in db.scalars(
                    select(Video.provider)
                    .join(SignalVideoEvidence, SignalVideoEvidence.video_id == Video.id)
                    .where(SignalVideoEvidence.signal_id == signal.id)
                ).all()
                if provider
            }
        )
    )
    if stored_mode in {"demo", "live"} and stored_providers:
        if providers and providers != stored_providers:
            # The underlying source changed after this signal was calculated.
            # Hide it until it is rebuilt instead of relabelling stale evidence.
            return "unavailable", providers
        return str(stored_mode), stored_providers
    modes = {evidence_mode_for_provider(provider) for provider in providers}
    if len(modes) == 1:
        return next(iter(modes)), providers
    return "unavailable", providers


def active_toy_signals(db: Session) -> list[ToySignal]:
    selected = selected_evidence_mode(db)
    if selected == "unavailable":
        return []
    signals = db.scalars(
        select(ToySignal).order_by(ToySignal.opportunity_score.desc())
    ).all()
    return [
        signal
        for signal in signals
        if signal_evidence_identity(db, signal)[0] == selected
    ]


def _stable_key(
    provider: str,
    evidence_mode: str,
    category: str,
    mechanism: str,
    market: str,
    language: str,
) -> str:
    identity = json.dumps(
        {
            "provider": provider,
            "evidence_mode": evidence_mode,
            "toy_category": category,
            "content_mechanism": mechanism,
            "market": market,
            "language": language,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(identity.encode("utf-8")).hexdigest()


def _legacy_stable_key(
    category: str, mechanism: str, market: str, language: str
) -> str:
    """Stable key used before provider/mode isolation, for in-place adoption."""

    identity = json.dumps(
        {
            "toy_category": category,
            "content_mechanism": mechanism,
            "market": market,
            "language": language,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(identity.encode("utf-8")).hexdigest()


def _freshness_score(latest: datetime | None, now: datetime) -> float:
    if latest is None:
        return 0.0
    hours = max(0.0, (_utc_naive(now) - _utc_naive(latest)).total_seconds() / 3600)
    if hours <= 6:
        return 100.0
    if hours <= 24:
        return 70.0
    if hours <= 72:
        return 30.0
    return 0.0


def _bounded_log(value: float | None, reference: float) -> float | None:
    if value is None:
        return None
    if value <= 0:
        return 0.0
    return min(100.0, 100 * log1p(value) / log1p(reference))


def _provider_health(db: Session, providers: set[str]) -> tuple[float, dict]:
    query = select(ProviderRun).order_by(ProviderRun.started_at.desc()).limit(50)
    runs = db.scalars(query).all()
    run = next((candidate for candidate in runs if candidate.provider in providers), None)
    if run is None:
        return 50.0, {"status": "Unknown", "provider_run_id": None}
    status = run.status.casefold()
    if status in {"success", "succeeded", "completed", "ready"}:
        score = 100.0
    elif status in {"failed", "aborted", "timed_out", "timed-out"}:
        score = 0.0
    else:
        score = 50.0
    return score, {"status": run.status, "provider_run_id": run.id}


def _saturation(
    evidence: list[CalculatedVideoEvidence],
    unique_creators: int,
    first_detected: datetime,
    now: datetime,
) -> tuple[float, str, dict]:
    post_count = len(evidence)
    creator_counts = Counter(item.video.creator_id for item in evidence)
    concentration = max(creator_counts.values()) / post_count if post_count else 1.0
    age_days = max(0.0, (_utc_naive(now) - _utc_naive(first_detected)).total_seconds() / 86400)
    components = {
        "creator_breadth": min(100.0, unique_creators / 10 * 100),
        "post_density": min(100.0, post_count / 20 * 100),
        "creator_diffusion": max(0.0, (1 - concentration) * 100),
        "signal_age": min(100.0, age_days / 30 * 100),
    }
    score = (
        components["creator_breadth"] * 0.45
        + components["post_density"] * 0.20
        + components["creator_diffusion"] * 0.20
        + components["signal_age"] * 0.15
    )
    label = "High" if score >= 70 else "Medium" if score >= 40 else "Low"
    return round(score, 1), label, components


def _confidence(
    db: Session,
    evidence: list[CalculatedVideoEvidence],
    unique_creators: int,
    latest_freshness: datetime | None,
    providers: set[str],
    now: datetime,
) -> tuple[float, str, dict]:
    post_count = len(evidence)
    snapshot_adequacy = (
        sum(min(item.view_snapshot_count / 3, 1) for item in evidence) / post_count * 100
        if post_count
        else 0.0
    )
    completeness = (
        sum(item.completeness for item in evidence) / post_count * 100 if post_count else 0.0
    )
    freshness = _freshness_score(latest_freshness, now)
    provider_health, provider_evidence = _provider_health(db, providers)
    velocities = [item.velocity for item in evidence if item.velocity is not None]
    mixed_direction = any(value > 0 for value in velocities) and any(
        value <= 0 for value in velocities
    )
    creator_evidence = round(min(100.0, unique_creators / 5 * 100), 1)
    cohort_evidence = round(min(100.0, post_count / 10 * 100), 1)
    market_velocities: dict[str, list[float]] = defaultdict(list)
    observed_markets = sorted(
        {
            (item.video.collection_market or item.video.market).upper()
            for item in evidence
            if item.video.collection_market or item.video.market
        }
    )
    for item in evidence:
        if item.velocity is None:
            continue
        observed_market = (item.video.collection_market or item.video.market).upper()
        market_velocities[observed_market].append(item.velocity)
    directional_markets = {
        market: median(values) > 0
        for market, values in market_velocities.items()
        if values
    }
    if len(directional_markets) >= 2:
        positive_markets = sum(directional_markets.values())
        majority = max(positive_markets, len(directional_markets) - positive_markets)
        market_consistency = majority / len(directional_markets) * 100
        market_status = "Cross-market direction observed"
        market_explanation = (
            f"{majority} of {len(directional_markets)} markets agree on the observed "
            "velocity direction; collection market is not audience geography."
        )
    else:
        market_consistency = 0.0
        market_status = "No cross-market confirmation"
        market_explanation = (
            "Evidence comes from one collection market only; it does not confirm "
            "that the pattern is consistent across markets or describe audience geography."
        )
    components = {
        "snapshot_adequacy": round(snapshot_adequacy, 1),
        "independent_creator_evidence": creator_evidence,
        "required_field_completeness": round(completeness, 1),
        "freshness": round(freshness, 1),
        "cohort_size": cohort_evidence,
        "market_consistency": round(market_consistency, 1),
        "market_evidence": {
            "status": market_status,
            "markets": observed_markets,
            "markets_with_directional_evidence": sorted(directional_markets),
            "explanation": market_explanation,
        },
        "provider_health": round(provider_health, 1),
        "provider_evidence": provider_evidence,
        "contradictory_direction": mixed_direction,
    }
    score = (
        snapshot_adequacy * 0.20
        + creator_evidence * 0.15
        + completeness * 0.20
        + freshness * 0.15
        + cohort_evidence * 0.10
        + market_consistency * 0.05
        + provider_health * 0.10
        - (10 if mixed_direction else 0)
    )
    score = max(0.0, min(100.0, score))
    label = "High" if score >= 75 else "Medium" if score >= 50 else "Low"
    return round(score, 1), label, components


def _opportunity_score(
    evidence: list[CalculatedVideoEvidence],
    unique_creators: int,
    freshness_score: float,
    saturation_score: float,
) -> tuple[float, dict, list[str]]:
    velocities = [item.velocity for item in evidence if item.velocity is not None]
    accelerations = [item.acceleration for item in evidence if item.acceleration is not None]
    share_save_rates = [
        item.share_save_rate for item in evidence if item.share_save_rate is not None
    ]
    median_velocity = median(velocities) if velocities else None
    median_acceleration = median(accelerations) if accelerations else None
    median_share_save = median(share_save_rates) if share_save_rates else None
    completeness = sum(item.completeness for item in evidence) / len(evidence) * 100
    components: dict[str, float | None] = {
        "velocity": _bounded_log(median_velocity, 100_000),
        "acceleration": _bounded_log(median_acceleration, 50_000),
        "creator_diversity": min(100.0, unique_creators / 10 * 100),
        "share_save_signal": (
            min(100.0, median_share_save / 0.10 * 100)
            if median_share_save is not None
            else None
        ),
        "freshness": freshness_score,
        "toy_relevance": 100.0,
        "evidence_completeness": completeness,
        "saturation_penalty": saturation_score,
    }
    missing = [
        name
        for name in ("velocity", "acceleration", "share_save_signal")
        if components[name] is None
    ]
    weighted = (
        (components["velocity"] or 0) * 0.25
        + (components["acceleration"] or 0) * 0.20
        + (components["creator_diversity"] or 0) * 0.15
        + (components["share_save_signal"] or 0) * 0.10
        + (components["freshness"] or 0) * 0.10
        + (components["toy_relevance"] or 0) * 0.10
        + (components["evidence_completeness"] or 0) * 0.10
        - saturation_score * 0.20
    )
    return round(max(0.0, min(100.0, weighted)), 1), components, missing


def _lifecycle(
    evidence: list[CalculatedVideoEvidence],
    unique_creators: int,
    saturation_score: float,
    opportunity_score: float,
) -> tuple[str, dict]:
    velocities = [item.velocity for item in evidence if item.velocity is not None]
    accelerations = [item.acceleration for item in evidence if item.acceleration is not None]
    current_views = [item.latest_views for item in evidence if item.latest_views is not None]
    facts = {
        "posts_with_velocity": len(velocities),
        "posts_with_acceleration": len(accelerations),
        "median_velocity": _rounded(median(velocities) if velocities else None),
        "median_acceleration": _rounded(median(accelerations) if accelerations else None),
        "median_current_views": _rounded(median(current_views) if current_views else None),
        "unique_creators": unique_creators,
    }
    if len(velocities) < 2 or unique_creators < 2:
        return "Insufficient evidence", facts
    median_velocity = median(velocities)
    median_acceleration = median(accelerations) if len(accelerations) >= 2 else None
    median_views = median(current_views) if current_views else 0
    if median_acceleration is not None and median_acceleration < 0:
        return "Declining", facts
    if saturation_score >= 70 and (median_acceleration is None or median_acceleration <= 0):
        return "Saturated", facts
    if (
        len(velocities) >= 5
        and unique_creators >= 5
        and median_views >= 250_000
        and median_velocity > 0
    ):
        return "Viral", facts
    if (
        len(accelerations) >= 3
        and unique_creators >= 3
        and median_acceleration is not None
        and median_acceleration > 0
        and opportunity_score >= 70
    ):
        return "Breakout", facts
    if median_acceleration is not None and median_acceleration > 0:
        return "Accelerating", facts
    if median_velocity > 0:
        return "Emerging", facts
    return "Insufficient evidence", facts


def _apply_recurring_lifecycle(
    *,
    base_lifecycle: str,
    lifecycle_facts: dict,
    previous_signal: ToySignal | None,
    latest_freshness: datetime | None,
) -> tuple[str, dict]:
    """Promote a signal to Recurring only from persisted, separated evidence.

    A single calculation can never create a recurring pattern. The first
    qualification needs a previously persisted active lifecycle, a genuinely
    newer observation window separated by at least 72 hours, and positive
    re-acceleration in the current evidence. Once qualified, idempotent rebuilds
    and further positively accelerating observations retain the Recurring state.
    """

    previous_lifecycle = previous_signal.lifecycle if previous_signal else None
    previous_freshness = (
        previous_signal.data_freshness_at if previous_signal is not None else None
    )
    current_acceleration = lifecycle_facts.get("median_acceleration")
    reaccelerating = (
        isinstance(current_acceleration, (int, float)) and current_acceleration > 0
    )
    newer_observation = bool(
        latest_freshness
        and previous_freshness
        and _utc_naive(latest_freshness) > _utc_naive(previous_freshness)
    )
    observation_gap_hours: float | None = None
    if latest_freshness and previous_freshness:
        observation_gap_hours = max(
            0.0,
            (
                _utc_naive(latest_freshness) - _utc_naive(previous_freshness)
            ).total_seconds()
            / 3600,
        )

    first_qualification = bool(
        previous_lifecycle in RECURRING_PRIOR_LIFECYCLES - {"Recurring"}
        and newer_observation
        and observation_gap_hours is not None
        and observation_gap_hours >= RECURRING_OBSERVATION_GAP_HOURS
        and reaccelerating
        and base_lifecycle in {"Accelerating", "Breakout", "Viral"}
    )
    retained_qualification = bool(
        previous_lifecycle == "Recurring"
        and (
            not newer_observation
            or (
                reaccelerating
                and base_lifecycle in {"Accelerating", "Breakout", "Viral"}
            )
        )
    )
    recurring = first_qualification or retained_qualification

    reason = "Not qualified"
    if first_qualification:
        reason = (
            "Previously persisted active signal re-accelerated in a new observation "
            f"window {observation_gap_hours:.1f} hours later."
        )
    elif retained_qualification:
        reason = (
            "Previously qualified recurrence remains supported; no unchanged rebuild "
            "can create a new recurrence claim."
        )
    elif previous_signal is None:
        reason = "No persisted prior signal assessment exists."
    elif not newer_observation:
        reason = "No genuinely newer observation window exists."
    elif observation_gap_hours is not None and observation_gap_hours < RECURRING_OBSERVATION_GAP_HOURS:
        reason = (
            f"Observation gap is {observation_gap_hours:.1f} hours; at least "
            f"{RECURRING_OBSERVATION_GAP_HOURS:.0f} hours is required."
        )
    elif not reaccelerating:
        reason = "Current evidence does not show positive re-acceleration."

    facts = {
        **lifecycle_facts,
        "base_lifecycle": base_lifecycle,
        "recurrence": {
            "qualified": recurring,
            "previous_lifecycle": previous_lifecycle,
            "previous_observed_at": (
                _utc_naive(previous_freshness).isoformat()
                if previous_freshness
                else None
            ),
            "current_observed_at": (
                _utc_naive(latest_freshness).isoformat()
                if latest_freshness
                else None
            ),
            "observation_gap_hours": _rounded(observation_gap_hours),
            "minimum_gap_hours": RECURRING_OBSERVATION_GAP_HOURS,
            "newer_observation": newer_observation,
            "reaccelerating": reaccelerating,
            "reason": reason,
        },
    }
    return ("Recurring" if recurring else base_lifecycle), facts


def _safety_state(evidence: list[CalculatedVideoEvidence]) -> str:
    statuses = {item.video.safety_status.casefold() for item in evidence}
    if any(item.video.safety_flags for item in evidence) or statuses - {
        "clear",
        "no automated concern",
    }:
        return "Review required"
    if statuses:
        return "Clear"
    return "Unknown"


def _recommended_decision(
    lifecycle: str,
    confidence: str,
    opportunity_score: float,
    saturation_score: float,
    safety_state: str,
) -> str:
    if safety_state == "Review required" or lifecycle in {"Saturated", "Declining"}:
        return "Avoid"
    if lifecycle in {"Accelerating", "Breakout"} and confidence in {"Medium", "High"}:
        if opportunity_score >= 55 and saturation_score < 70:
            return "Act"
    return "Monitor"


def _top_values(values: list[str], limit: int = 10) -> list[str]:
    counts = Counter(value for value in values if value)
    return [value for value, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def build_or_update_toy_signals(
    db: Session,
    now: datetime | None = None,
    *,
    evidence_mode: str | None = None,
) -> list[ToySignal]:
    calculated_at = _utc_naive(now or datetime.now(UTC))
    selected_mode = evidence_mode or configured_evidence_mode()
    if selected_mode not in {"demo", "live"}:
        return []
    videos = active_videos(db, mode=selected_mode)
    grouped: dict[
        tuple[str, str, str, str, str], list[CalculatedVideoEvidence]
    ] = defaultdict(list)

    for video in videos:
        classification = classify_toy_content(video.caption, video.hashtags or [])
        category = (
            video.toy_category
            or classification.toy_category
            or _legacy_toy_category(video.product_category)
        )
        if category is None:
            continue
        mechanism = video.content_mechanism or classification.content_mechanism or UNKNOWN_MECHANISM
        video.toy_category = category
        video.content_mechanism = mechanism
        if classification.safety_flags:
            video.safety_flags = list(
                dict.fromkeys([*(video.safety_flags or []), *classification.safety_flags])
            )
        snapshots = db.scalars(
            select(Snapshot)
            .where(
                Snapshot.video_id == video.id,
                Snapshot.source == video.provider,
            )
            .order_by(Snapshot.collected_at)
        ).all()
        calculated = calculate_video_evidence(video, snapshots)
        grouped[(video.provider, category, mechanism, video.market, video.language)].append(
            calculated
        )

    sounds = {sound.id: sound for sound in db.scalars(select(Sound)).all()}
    updated: list[ToySignal] = []
    for (provider, category, mechanism, market, language), evidence in sorted(
        grouped.items()
    ):
        provider_mode = evidence_mode_for_provider(provider)
        key = _stable_key(
            provider, provider_mode, category, mechanism, market, language
        )
        signal = db.scalar(select(ToySignal).where(ToySignal.stable_key == key))
        if signal is None:
            legacy = db.scalar(
                select(ToySignal).where(
                    ToySignal.stable_key
                    == _legacy_stable_key(category, mechanism, market, language)
                )
            )
            if legacy is not None:
                legacy_mode, legacy_providers = signal_evidence_identity(db, legacy)
                if legacy_mode == provider_mode and legacy_providers == (provider,):
                    legacy.stable_key = key
                    signal = legacy
        first_observations = [
            item.first_observed_at or item.video.first_observed_at or item.video.published_at
            for item in evidence
        ]
        first_detected = min(_utc_naive(value) for value in first_observations)
        latest_freshness_values = [item.freshness_at for item in evidence if item.freshness_at]
        latest_freshness = (
            max(_utc_naive(value) for value in latest_freshness_values)
            if latest_freshness_values
            else None
        )
        creator_ids = {item.video.creator_id for item in evidence}
        providers = {item.video.provider for item in evidence}
        saturation_score, saturation_label, saturation_components = _saturation(
            evidence, len(creator_ids), first_detected, calculated_at
        )
        confidence_score, confidence_label, confidence_components = _confidence(
            db,
            evidence,
            len(creator_ids),
            latest_freshness,
            providers,
            calculated_at,
        )
        freshness_score = _freshness_score(latest_freshness, calculated_at)
        opportunity_score, opportunity_components, opportunity_missing = _opportunity_score(
            evidence, len(creator_ids), freshness_score, saturation_score
        )
        base_lifecycle, lifecycle_evidence = _lifecycle(
            evidence, len(creator_ids), saturation_score, opportunity_score
        )
        lifecycle, lifecycle_evidence = _apply_recurring_lifecycle(
            base_lifecycle=base_lifecycle,
            lifecycle_facts=lifecycle_evidence,
            previous_signal=signal,
            latest_freshness=latest_freshness,
        )
        safety_state = _safety_state(evidence)
        decision = _recommended_decision(
            lifecycle,
            confidence_label,
            opportunity_score,
            saturation_score,
            safety_state,
        )
        all_missing = sorted(
            set(opportunity_missing).union(
                *(set(item.missing_components) for item in evidence)
            )
        )
        velocities = [item.velocity for item in evidence if item.velocity is not None]
        accelerations = [item.acceleration for item in evidence if item.acceleration is not None]
        positive_posts = sum(item.velocity is not None and item.velocity > 0 for item in evidence)
        negative_posts = sum(item.velocity is not None and item.velocity <= 0 for item in evidence)
        supporting = (
            f"{positive_posts} of {len(evidence)} posts have observed positive velocity; "
            f"{len(creator_ids)} independent creators; latest evidence "
            f"{latest_freshness.isoformat() if latest_freshness else 'unavailable'}."
        )
        contradictions: list[str] = []
        if negative_posts:
            contradictions.append(f"{negative_posts} posts are flat or declining")
        if all_missing:
            contradictions.append("Missing: " + ", ".join(all_missing))
        if len(creator_ids) < 2:
            contradictions.append("Fewer than two independent creators")
        contradictory = "; ".join(contradictions) or "No material contradiction observed in sample."

        if signal is None:
            signal = ToySignal(
                stable_key=key,
                title=f"{mechanism} in {category}",
                toy_category=category,
                content_mechanism=mechanism,
                first_detected_at=first_detected,
                created_at=calculated_at,
            )
            db.add(signal)
            db.flush()
        signal.title = f"{mechanism} in {category}"
        signal.toy_category = category
        signal.content_mechanism = mechanism
        signal.lifecycle = lifecycle
        signal.recommended_decision = decision
        signal.confidence = confidence_label
        signal.confidence_score = confidence_score
        signal.first_detected_at = min(signal.first_detected_at, first_detected)
        signal.last_calculated_at = calculated_at
        signal.data_freshness_at = latest_freshness
        signal.unique_creators = len(creator_ids)
        signal.post_count = len(evidence)
        signal.cohort_size = len(evidence)
        signal.markets = [market]
        signal.languages = [language]
        signal.related_hashtags = _top_values(
            [hashtag for item in evidence for hashtag in (item.video.hashtags or [])]
        )
        signal.related_sounds = _top_values(
            [
                sounds[item.video.sound_id].title
                for item in evidence
                if item.video.sound_id in sounds
            ]
        )
        signal.saturation = saturation_label
        signal.saturation_score = saturation_score
        signal.opportunity_score = opportunity_score
        signal.main_supporting_evidence = supporting
        signal.main_contradictory_evidence = contradictory
        signal.safety_state = safety_state
        signal.explanation = (
            f"{lifecycle}: evidence from {len(evidence)} posts and {len(creator_ids)} creators. "
            f"Recommendation is {decision}; this is a monitored-sample decision, not a "
            "virality prediction."
        )
        signal.components = {
            "evidence_mode": provider_mode,
            "evidence_providers": sorted(providers),
            "lifecycle": lifecycle_evidence,
            "confidence": confidence_components,
            "saturation": saturation_components,
            "opportunity": opportunity_components,
            "observed_median_velocity": _rounded(median(velocities) if velocities else None),
            "observed_median_acceleration": _rounded(
                median(accelerations) if accelerations else None
            ),
            "creator_baseline": {"status": "Unavailable unless observed", "value": None},
            "coverage": "Configured monitored sample",
        }
        signal.missing_components = all_missing
        signal.score_version = SCORE_VERSION
        signal.updated_at = calculated_at
        db.flush()

        existing_memberships = {
            membership.video_id: membership
            for membership in db.scalars(
                select(SignalVideoEvidence).where(SignalVideoEvidence.signal_id == signal.id)
            ).all()
        }
        current_video_ids = {item.video.id for item in evidence}
        for video_id, existing_membership in existing_memberships.items():
            if video_id not in current_video_ids:
                db.delete(existing_membership)
        for item in evidence:
            membership_row = existing_memberships.get(item.video.id)
            if membership_row is None:
                membership_row = SignalVideoEvidence(
                    signal_id=signal.id, video_id=item.video.id
                )
                db.add(membership_row)
            is_supporting = item.velocity is not None and item.velocity > 0
            membership_row.evidence_type = (
                "supporting" if is_supporting else "contradictory" if item.velocity is not None else "context"
            )
            membership_row.supporting = is_supporting
            membership_row.weight = round(item.completeness, 3)
            membership_row.rationale = (
                "Observed positive velocity."
                if is_supporting
                else "Observed flat or declining velocity."
                if item.velocity is not None
                else "Not enough observations to calculate velocity."
            )
            membership_row.metrics = item.metrics()
            membership_row.observed_at = item.freshness_at
            membership_row.updated_at = calculated_at
        updated.append(signal)

    db.commit()
    return updated
