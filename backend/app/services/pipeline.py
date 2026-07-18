from datetime import UTC, datetime
from hashlib import sha256
from math import log1p
from statistics import median
from collections import defaultdict
from typing import Any
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.domain.toys import classify_creator_type, classify_toy_content
from app.models import Creator, Snapshot, Sound, Video, ViralScore
from app.providers.base import ProviderVideo
from app.services.reporting import generate_report

TOY={"toy","parenting","board_game","educational","collectible","family"}
UNSAFE=("niebezpieczne","dangerous challenge","choking","gambling","alcohol","medical cure")


def _utc_naive(value: datetime) -> datetime:
    """Normalise provider timestamps without inventing a timezone or observation."""

    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def _merge_missing(*values: list[str] | None) -> list[str]:
    return sorted({field for fields in values if fields for field in fields if field})


def _provider_scoped_storage_id(
    db: Session,
    model: Any,
    external_id: str,
    provider: str,
) -> str:
    """Avoid cross-provider relabelling when external identifiers collide.

    Existing rows retain their original external identifier. A colliding row
    from another provider gets a deterministic, length-bounded storage key.
    """

    existing = db.scalar(select(model).where(model.provider_id == external_id))
    if existing is None or existing.provider == provider:
        return external_id
    prefix = sha256(provider.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}:{external_id}"[:100]


def classify(text:str,hashtags:list[str])->tuple[str,str]:
    s=(text+" "+" ".join(hashtags)).lower()
    if any(x in s for x in UNSAFE): return "safety_review_required","review"
    if any(x in s for x in ("stem toy","educational toy","learning toy")): return "educational","clear"
    if any(x in s for x in ("collectible","blind box")): return "collectible","clear"
    if any(x in s for x in ("parent","family","rodzin","gift for kid","kids activ")): return "family","clear"
    if any(x in s for x in ("toy","zabawk","building set","construction set","sensory","plush","doll","action figure","outdoor play")): return "toy","clear"
    if any(x in s for x in ("board game","card game")): return "board_game","clear"
    return "general","clear"
def product_category(text:str,hashtags:list[str])->str|None:
    s=(text+" "+" ".join(hashtags)).lower()
    for terms,label in [
        (("stem","educational","learning toy"),"Educational & STEM toys"),
        (("sensory","fidget"),"Sensory toys"),
        (("collectible","blind box"),"Collectibles"),
        (("construction","building set","blocks"),"Construction toys"),
        (("plush","stuffed toy"),"Plush toys"),
        (("doll","action figure"),"Dolls & action figures"),
        (("outdoor toy","outdoor play"),"Outdoor toys"),
        (("parent","gift for kid","gift idea"),"Parent & gift-buyer content"),
        (("toy","zabawk"),"Children's toys"),
    ]:
        if any(term in s for term in terms): return label
    return None


def ingest(
    db: Session,
    rows: list[ProviderVideo],
    collected_at: datetime | None = None,
    *,
    provider_run_id: int | None = None,
    collection_market: str | None = None,
) -> dict[str, int]:
    """Append provider observations while keeping provenance explicit.

    ``collection_market`` is the market used to scope the provider query. It is
    not creator or audience geography. Engagement values are copied verbatim,
    including ``None`` for fields the provider did not return.

    The optional keyword-only arguments preserve every legacy caller while
    allowing live provider runs to link both the discovered video and each
    immutable snapshot to a persisted ``ProviderRun``.
    """

    default_observed_at = _utc_naive(
        collected_at or datetime.now(UTC).replace(tzinfo=None)
    )
    new = duplicates = snapshots_added = snapshot_duplicates = 0
    for r in rows:
        observed_at = _utc_naive(collected_at or r.retrieved_at or default_observed_at)
        freshness_at = _utc_naive(collected_at or r.freshness_at or observed_at)
        classified_category, safety = classify(r.caption, r.hashtags)
        toy_classification = classify_toy_content(r.caption, r.hashtags)
        explicit_collection_market = (collection_market or r.market or "ZZ").upper()

        creator_storage_id = _provider_scoped_storage_id(
            db, Creator, r.creator_id, r.provider
        )
        creator = db.scalar(
            select(Creator).where(Creator.provider_id == creator_storage_id)
        )
        if creator is None:
            account_region = (
                r.creator_account_region.upper() if r.creator_account_region else None
            )
            creator = Creator(
                provider_id=creator_storage_id,
                username=r.username,
                display_name=r.creator_display_name,
                profile_url=r.creator_profile_url,
                # ``region`` is a compatibility field, never audience geography.
                region=account_region or "ZZ",
                account_region=account_region,
                followers=r.creator_followers,
                verified=r.creator_verified,
                niche=(
                    "toy"
                    if toy_classification.toy_category or classified_category in TOY
                    else "general"
                ),
                creator_type=classify_creator_type(
                    " ".join(
                        value
                        for value in (
                            r.caption,
                            r.creator_display_name,
                            r.username,
                        )
                        if value
                    )
                ),
                apparent_minor=None,
                provider=r.provider,
                raw_reference=r.raw_reference,
                missing_fields=list(r.missing_fields),
                last_observed_at=observed_at,
            )
            db.add(creator)
            db.flush()
        else:
            creator.username = r.username or creator.username
            creator.display_name = r.creator_display_name or creator.display_name
            creator.profile_url = r.creator_profile_url or creator.profile_url
            creator.followers = (
                r.creator_followers
                if r.creator_followers is not None
                else creator.followers
            )
            creator.verified = (
                r.creator_verified if r.creator_verified is not None else creator.verified
            )
            if r.creator_account_region:
                creator.account_region = r.creator_account_region.upper()
                creator.region = r.creator_account_region.upper()
            creator.provider = r.provider or creator.provider
            creator.raw_reference = r.raw_reference or creator.raw_reference
            creator.missing_fields = _merge_missing(creator.missing_fields, r.missing_fields)
            creator.last_observed_at = observed_at

        sound = None
        if r.sound_id:
            sound_storage_id = _provider_scoped_storage_id(
                db, Sound, r.sound_id, r.provider
            )
            sound = db.scalar(
                select(Sound).where(Sound.provider_id == sound_storage_id)
            )
            sound_missing = list(r.missing_fields)
            if not r.sound_title:
                sound_missing = _merge_missing(sound_missing, ["sound_title"])
            if sound is None:
                sound = Sound(
                    provider_id=sound_storage_id,
                    title=r.sound_title or "Unknown sound",
                    commercial_status="unknown",
                    provider=r.provider,
                    raw_reference=r.raw_reference,
                    missing_fields=sound_missing,
                    last_observed_at=observed_at,
                )
                db.add(sound)
                db.flush()
            else:
                sound.title = r.sound_title or sound.title
                sound.provider = r.provider or sound.provider
                sound.raw_reference = r.raw_reference or sound.raw_reference
                sound.missing_fields = _merge_missing(sound.missing_fields, sound_missing)
                sound.last_observed_at = observed_at

        video_storage_id = _provider_scoped_storage_id(db, Video, r.id, r.provider)
        video = db.scalar(
            select(Video).where(Video.provider_id == video_storage_id)
        )
        current_discovery_queries = list(r.discovery_queries)
        discovery_query: dict[str, Any] = {
            "collection_type": r.collection_type,
            "queries": current_discovery_queries,
            "context": dict(r.discovery_context),
            "provider_external_run_id": r.provider_run_id,
            "dataset_id": r.dataset_id,
        }
        safety_flags = list(toy_classification.safety_flags)
        if safety == "review" and not safety_flags:
            safety_flags = ["Manual safety review required"]
        if video is None:
            video = Video(
                provider_id=video_storage_id,
                url=r.url,
                creator_id=creator.id,
                sound_id=sound.id if sound else None,
                provider_run_id=provider_run_id,
                caption=r.caption,
                hashtags=list(r.hashtags),
                published_at=_utc_naive(r.published_at),
                language=r.language or "und",
                provider_language=r.language or None,
                detected_language=None,
                # Legacy ``market`` now means collection scope, not audience.
                market=explicit_collection_market,
                collection_market=explicit_collection_market,
                category=classified_category,
                product_category=product_category(r.caption, r.hashtags),
                toy_category=toy_classification.toy_category,
                content_mechanism=toy_classification.content_mechanism,
                child_featured=None,
                safety_status=safety,
                safety_flags=safety_flags,
                availability_status=r.availability_status,
                discovery_query=discovery_query,
                provider=r.provider,
                raw_reference=r.raw_reference,
                schema_fingerprint=r.schema_fingerprint,
                missing_fields=list(r.missing_fields),
                first_observed_at=observed_at,
                last_observed_at=observed_at,
            )
            db.add(video)
            db.flush()
            new += 1
        else:
            duplicates += 1
            existing_discovery = dict(video.discovery_query or {})
            merged_queries = list(
                dict.fromkeys(
                    [
                        *list(existing_discovery.get("queries") or []),
                        *current_discovery_queries,
                    ]
                )
            )
            external_run_ids = list(
                dict.fromkeys(
                    [
                        *list(existing_discovery.get("provider_external_run_ids") or []),
                        *(
                            [str(existing_discovery["provider_external_run_id"])]
                            if existing_discovery.get("provider_external_run_id")
                            else []
                        ),
                        *(
                            [str(r.provider_run_id)] if r.provider_run_id else []
                        ),
                    ]
                )
            )
            dataset_ids = list(
                dict.fromkeys(
                    [
                        *list(existing_discovery.get("dataset_ids") or []),
                        *(
                            [str(existing_discovery["dataset_id"])]
                            if existing_discovery.get("dataset_id")
                            else []
                        ),
                        *([str(r.dataset_id)] if r.dataset_id else []),
                    ]
                )
            )
            video.url = r.url or video.url
            video.creator_id = creator.id
            video.sound_id = sound.id if sound else video.sound_id
            video.caption = r.caption or video.caption
            video.hashtags = list(r.hashtags) if r.hashtags else video.hashtags
            video.language = r.language or video.language
            video.provider_language = r.language or video.provider_language
            # The first discovery scope remains the canonical video scope. Every
            # later collection scope is still recoverable through ProviderRun.
            video.collection_market = video.collection_market or explicit_collection_market
            video.category = classified_category
            video.product_category = product_category(r.caption, r.hashtags)
            video.toy_category = toy_classification.toy_category or video.toy_category
            video.content_mechanism = (
                toy_classification.content_mechanism or video.content_mechanism
            )
            video.safety_status = (
                "review" if video.safety_status == "review" or safety == "review" else "clear"
            )
            video.safety_flags = _merge_missing(video.safety_flags, safety_flags)
            video.availability_status = r.availability_status
            video.discovery_query = {
                **existing_discovery,
                "queries": merged_queries,
                "context": {
                    **dict(existing_discovery.get("context") or {}),
                    **dict(r.discovery_context),
                },
                "provider_external_run_ids": external_run_ids,
                "dataset_ids": dataset_ids,
                "latest_collection_type": r.collection_type,
            }
            video.provider = r.provider or video.provider
            video.raw_reference = r.raw_reference or video.raw_reference
            video.schema_fingerprint = r.schema_fingerprint or video.schema_fingerprint
            video.missing_fields = _merge_missing(video.missing_fields, r.missing_fields)
            video.last_observed_at = observed_at

        duplicate_predicate = Snapshot.collected_at == observed_at
        if provider_run_id is not None:
            duplicate_predicate = or_(
                duplicate_predicate,
                Snapshot.provider_run_id == provider_run_id,
            )
        existing_snapshot = db.scalar(
            select(Snapshot).where(
                Snapshot.video_id == video.id,
                duplicate_predicate,
            )
        )
        if existing_snapshot is None:
            metrics = r.metrics
            db.add(
                Snapshot(
                    video_id=video.id,
                    provider_run_id=provider_run_id,
                    collected_at=observed_at,
                    freshness_at=freshness_at,
                    views=metrics.get("views"),
                    likes=metrics.get("likes"),
                    comments=metrics.get("comments"),
                    shares=metrics.get("shares"),
                    favourites=metrics.get("favourites"),
                    creator_follower_count=r.creator_followers,
                    availability_state=r.availability_status,
                    missing_fields=list(r.missing_fields),
                    source=r.provider,
                )
            )
            snapshots_added += 1
        else:
            snapshot_duplicates += 1

    db.commit()
    return {
        "new": new,
        "duplicates": duplicates,
        "snapshots_added": snapshots_added,
        "snapshot_duplicates": snapshot_duplicates,
        "total": len(rows),
    }
def _pct(values: list[float], value: float) -> float:
    return 100 * sum(candidate <= value for candidate in values) / max(1, len(values))


def _observed(snapshot: Snapshot, field: str) -> int:
    value = getattr(snapshot, field)
    if value is None:
        raise ValueError(f"Missing observed metric: {field}")
    return value


def _age_band(hours: float) -> str:
    for limit, label in [
        (6, "0-6h"),
        (12, "6-12h"),
        (24, "12-24h"),
        (48, "24-48h"),
        (72, "48-72h"),
        (168, "3-7d"),
        (720, "7-30d"),
    ]:
        if hours <= limit:
            return label
    return "30d+"


def _weighted_percentile_score(
    percentiles: dict[str, float], weights: dict[str, float]
) -> float:
    available = {key: weight for key, weight in weights.items() if key in percentiles}
    total_weight = sum(available.values())
    if total_weight == 0:
        return 0.0
    return sum(percentiles[key] * weight for key, weight in available.items()) / total_weight


def score_all(db: Session) -> int:
    """Maintain the legacy per-video scores without manufacturing missing evidence."""

    calculations: list[dict[str, Any]] = []
    now = datetime.now(UTC).replace(tzinfo=None)
    for video in db.scalars(select(Video).where(Video.removed.is_(False))).all():
        snapshots = db.scalars(
            select(Snapshot)
            .where(Snapshot.video_id == video.id)
            .order_by(Snapshot.collected_at)
        ).all()
        complete_snapshots = [
            snapshot
            for snapshot in snapshots
            if all(
                getattr(snapshot, field) is not None
                for field in ("views", "likes", "comments", "shares")
            )
        ]
        if len(complete_snapshots) < 2:
            continue
        first, latest = complete_snapshots[0], complete_snapshots[-1]
        hours = max((latest.collected_at - first.collected_at).total_seconds() / 3600, 0.1)
        growth = _observed(latest, "views") - _observed(first, "views")
        velocity = growth / hours
        acceleration: float | None = None
        if len(complete_snapshots) >= 3:
            third_last, previous = complete_snapshots[-3], complete_snapshots[-2]
            first_interval = max(
                (previous.collected_at - third_last.collected_at).total_seconds() / 3600,
                0.1,
            )
            second_interval = max(
                (latest.collected_at - previous.collected_at).total_seconds() / 3600,
                0.1,
            )
            acceleration = (
                (_observed(latest, "views") - _observed(previous, "views"))
                / second_interval
                - (_observed(previous, "views") - _observed(third_last, "views"))
                / first_interval
            )
        current_views = _observed(latest, "views")
        engagement = (
            _observed(latest, "likes")
            + _observed(latest, "comments")
            + _observed(latest, "shares")
        ) / max(current_views, 1)
        share_rate = _observed(latest, "shares") / max(current_views, 1)
        anomaly = (
            70
            if growth < 0 or growth > max(_observed(first, "views") * 5, 2_000_000)
            else 0
        )
        share_velocity = (
            _observed(latest, "shares") - _observed(first, "shares")
        ) / hours
        calculations.append(
            {
                "video": video,
                "latest": latest,
                "growth": growth,
                "velocity": velocity,
                "acceleration": acceleration,
                "engagement": engagement,
                "share_rate": share_rate,
                "share_velocity": share_velocity,
                "anomaly": anomaly,
                "snapshots": complete_snapshots,
                # Publication time is observed provider data; this is not age inference.
                "age_hours": max(0, (now - video.published_at).total_seconds() / 3600),
            }
        )
    if not calculations:
        return 0

    creator_velocities: dict[int, list[float]] = defaultdict(list)
    for calculation in calculations:
        creator_velocities[calculation["video"].creator_id].append(
            calculation["velocity"]
        )

    spread_by_video: dict[int, int] = {}
    for calculation in calculations:
        video = calculation["video"]
        peers = {
            candidate["video"].creator_id
            for candidate in calculations
            if (
                video.sound_id is not None
                and candidate["video"].sound_id == video.sound_id
            )
            or bool(set(candidate["video"].hashtags) & set(video.hashtags))
        }
        spread_by_video[video.id] = len(peers)

    cohorts: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for calculation in calculations:
        video = calculation["video"]
        key = (
            video.market,
            video.language,
            video.category,
            _age_band(calculation["age_hours"]),
        )
        cohorts[key].append(calculation)
        calculation["cohort_key"] = key

    def metric_value(calculation: dict[str, Any], field: str) -> float | None:
        latest = calculation["latest"]
        video = calculation["video"]
        if field == "views":
            return log1p(max(float(_observed(latest, "views")), 0))
        if field == "view_velocity":
            return log1p(max(float(calculation["velocity"]), 0))
        if field == "share_rate":
            return float(calculation["share_rate"])
        if field == "engagement_rate":
            return float(calculation["engagement"])
        if field == "acceleration":
            value = calculation["acceleration"]
            return float(value) if value is not None else None
        if field == "creator_baseline_lift":
            observations = creator_velocities[video.creator_id]
            if len(observations) < 2:
                return None
            return float(calculation["velocity"]) / max(median(observations), 1)
        if field == "spread":
            return float(spread_by_video[video.id])
        if field == "percentage_growth":
            starting_views = _observed(latest, "views") - calculation["growth"]
            return max(0.0, calculation["growth"] / max(starting_views, 1))
        if field == "share_velocity":
            return max(0.0, float(calculation["share_velocity"]))
        if field == "novelty":
            return max(0.0, 100 - calculation["age_hours"] / 0.72)
        raise ValueError(f"Unknown score component: {field}")

    avs_weights = {
        "views": 0.25,
        "view_velocity": 0.25,
        "share_rate": 0.15,
        "engagement_rate": 0.10,
        "acceleration": 0.10,
        "creator_baseline_lift": 0.10,
        "spread": 0.05,
    }
    evs_weights = {
        "view_velocity": 0.30,
        "acceleration": 0.25,
        "percentage_growth": 0.15,
        "share_velocity": 0.10,
        "creator_baseline_lift": 0.10,
        "novelty": 0.10,
    }
    nps_weights = {
        "views": 0.30,
        "creator_baseline_lift": 0.25,
        "view_velocity": 0.20,
        "engagement_rate": 0.15,
        "share_rate": 0.10,
    }
    score_fields = set(avs_weights) | set(evs_weights) | set(nps_weights)

    for calculation in calculations:
        video = calculation["video"]
        latest = calculation["latest"]
        cohort = cohorts[calculation["cohort_key"]]
        raw = {
            field: metric_value(calculation, field) for field in sorted(score_fields)
        }
        percentiles: dict[str, float] = {}
        for field, raw_value in raw.items():
            if raw_value is None:
                continue
            cohort_values = [
                value
                for candidate in cohort
                if (value := metric_value(candidate, field)) is not None
            ]
            percentiles[field] = _pct(cohort_values, raw_value)
        avs = _weighted_percentile_score(percentiles, avs_weights)
        evs = _weighted_percentile_score(percentiles, evs_weights)
        nps = _weighted_percentile_score(percentiles, nps_weights)
        anomaly = calculation["anomaly"]
        adjusted = avs * (1 - 0.5 * anomaly / 100)
        freshness = max(0, (now - latest.freshness_at).total_seconds() / 3600)
        missing_components = sorted(
            [field for field, value in raw.items() if value is None]
            + list(video.missing_fields or [])
        )
        confidence_score = (
            min(100, len(calculation["snapshots"]) * 18)
            + min(20, len(cohort) * 2)
            - len(missing_components) * 10
            - (20 if freshness > 24 else 10 if freshness > 8 else 0)
        )
        confidence_score = max(0, min(100, confidence_score))
        confidence = (
            "High"
            if confidence_score >= 75
            else "Medium"
            if confidence_score >= 45
            else "Low"
        )
        components = {
            "raw": raw,
            "percentiles": percentiles,
            "avs_weights": avs_weights,
            "evs_weights": evs_weights,
            "nps_weights": nps_weights,
            "missing_components": missing_components,
            "evidence_type": "Demo" if video.provider == "mock" else "Derived",
        }
        row = db.scalar(select(ViralScore).where(ViralScore.video_id == video.id))
        if row is None:
            row = ViralScore(video_id=video.id)
            db.add(row)
        row.views_growth = calculation["growth"]
        row.views_per_hour = calculation["velocity"]
        row.acceleration = calculation["acceleration"]
        row.avs = round(avs, 1)
        row.evs = round(evs, 1)
        row.nps = round(nps, 1)
        row.anomaly = anomaly
        row.adjusted = round(adjusted, 1)
        row.confidence = confidence
        row.confidence_score = round(confidence_score, 1)
        row.components = components
        row.cohort = {
            "market": video.market,
            "language": video.language,
            "category": video.category,
            "video_age_band": _age_band(calculation["age_hours"]),
            "sample_size": len(cohort),
            "fallback": len(cohort) < 5,
        }
        row.score_version = "2.0"
        row.reason = (
            f"{confidence} confidence: {len(calculation['snapshots'])} snapshots, "
            f"cohort size {len(cohort)}, observed velocity "
            f"{calculation['velocity']:,.0f}/hr."
        )
    db.commit()
    return len(calculations)


def make_report(db:Session, *, user_key: str = "single-user"):
    return generate_report(db, user_key=user_key)
