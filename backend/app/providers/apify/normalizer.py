from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Iterable, TypedDict

from pydantic import ValidationError

from app.providers.base import ProviderVideo

from .errors import redact_text
from .inputs import ActorRequest
from .schemas import ActorAuthor, ActorMusic, ActorTikTokItem, ActorVideoMetadata


NORMALIZER_VERSION = "apify-toy-1.0"


class QuarantineQualityRecord(TypedDict):
    """Redacted provider-run contract consumed by quarantine persistence."""

    external_record_id: str
    record_index: int
    reason: str
    summary: str
    schema_fingerprint: str | None
    missing_fields: list[str]


@dataclass(frozen=True)
class QuarantinedRecord:
    index: int
    category: str
    summary: str
    schema_fingerprint: str | None

    def to_quality_record(self) -> QuarantineQualityRecord:
        """Return a redacted, persistence-ready representation.

        Invalid provider rows do not always have a trustworthy item id. The
        item position is therefore the safe external reference within its
        ProviderRun; raw input fields are intentionally not retained.
        """

        return {
            "external_record_id": f"dataset-item:{self.index}",
            "record_index": self.index,
            "reason": self.category,
            "summary": self.summary,
            "schema_fingerprint": self.schema_fingerprint,
            "missing_fields": [],
        }


@dataclass
class NormalizationResult:
    videos: list[ProviderVideo] = field(default_factory=list)
    quarantined: list[QuarantinedRecord] = field(default_factory=list)
    schema_fingerprints: set[str] = field(default_factory=set)


def schema_fingerprint(value: dict[str, Any]) -> str:
    keys = "|".join(sorted(str(key) for key in value))
    return sha256(keys.encode("utf-8")).hexdigest()[:16]


def _utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def normalize_items(
    items: Iterable[object],
    *,
    request: ActorRequest,
    run_id: str,
    dataset_id: str,
    retrieved_at: datetime,
    secrets: Iterable[str] = (),
) -> NormalizationResult:
    result = NormalizationResult()
    for index, raw in enumerate(items):
        if not isinstance(raw, dict):
            result.quarantined.append(
                QuarantinedRecord(index, "invalid_record", "Dataset item is not an object", None)
            )
            continue
        fingerprint = schema_fingerprint(raw)
        result.schema_fingerprints.add(fingerprint)
        try:
            item = ActorTikTokItem.model_validate(raw)
        except ValidationError as error:
            result.quarantined.append(
                QuarantinedRecord(
                    index,
                    "schema_validation",
                    redact_text(error, secrets),
                    fingerprint,
                )
            )
            continue
        if item.error_code or item.error_message:
            error_value = (item.error_code or item.error_message or "").lower()
            category = (
                "private_video"
                if "private" in error_value
                else "deleted_video"
                if any(value in error_value for value in ("deleted", "not-found", "not_found"))
                else "provider_item_error"
            )
            result.quarantined.append(
                QuarantinedRecord(
                    index,
                    category,
                    redact_text(item.error_code or item.error_message or "Provider item error", secrets),
                    fingerprint,
                )
            )
            continue
        try:
            result.videos.append(
                _normalize_item(
                    item,
                    request=request,
                    run_id=run_id,
                    dataset_id=dataset_id,
                    retrieved_at=retrieved_at,
                    fingerprint=fingerprint,
                )
            )
        except ValueError as error:
            result.quarantined.append(
                QuarantinedRecord(
                    index,
                    "missing_identity",
                    redact_text(error, secrets),
                    fingerprint,
                )
            )
    return result


def _normalize_item(
    item: ActorTikTokItem,
    *,
    request: ActorRequest,
    run_id: str,
    dataset_id: str,
    retrieved_at: datetime,
    fingerprint: str,
) -> ProviderVideo:
    author = item.author or ActorAuthor()
    required = {
        "provider_video_id": item.id,
        "canonical_url": item.canonical_url or item.submitted_url,
        "provider_creator_id": author.id,
        "username": author.name,
    }
    missing_identity = [name for name, value in required.items() if not value]
    if missing_identity:
        raise ValueError("Missing required identity fields: " + ", ".join(missing_identity))

    missing_fields: list[str] = []
    published_at = item.created_at
    if published_at is None and item.created_timestamp is not None:
        published_at = datetime.fromtimestamp(item.created_timestamp, tz=timezone.utc)
    if published_at is None:
        published_at = retrieved_at
        missing_fields.append("published_at")
    published_at = _utc_naive(published_at)

    if item.caption is None:
        missing_fields.append("caption")
    if item.provider_language is None:
        missing_fields.append("language")
    if item.hashtags is None:
        missing_fields.append("hashtags")
    if item.account_region is None:
        missing_fields.append("creator_account_region")

    metrics: dict[str, int | None] = {
        "views": item.views,
        "likes": item.likes,
        "comments": item.comments,
        "shares": item.shares,
        "saves": item.saves,
        # Compatibility alias for the current Snapshot model. New domain code should use saves.
        "favourites": item.saves,
    }
    missing_fields.extend(
        name for name in ("views", "likes", "comments", "shares", "saves") if metrics[name] is None
    )

    music = item.music or ActorMusic()
    if music.id is None:
        missing_fields.append("sound_id")
    metadata = item.video_metadata or ActorVideoMetadata()
    if metadata.duration is None:
        missing_fields.append("duration_seconds")

    hashtag_metadata = [
        {"provider_id": tag.id, "name": tag.name, "title": tag.title}
        for tag in item.hashtags or []
        if tag.name
    ]
    hashtags = [str(tag["name"]).removeprefix("#") for tag in hashtag_metadata]
    if item.discovery_query:
        query_values = [item.discovery_query]
    elif isinstance(item.input_value, str) and item.input_value.strip():
        query_values = [item.input_value.strip()]
    else:
        query_values = list(request.source_values)
    provider = f"apify:{request.actor_id}"
    raw_reference = (
        f"apify://{request.actor_id}/runs/{run_id}/datasets/{dataset_id}/video/{required['provider_video_id']}"
    )
    return ProviderVideo(
        id=str(required["provider_video_id"]),
        url=str(required["canonical_url"]),
        creator_id=str(required["provider_creator_id"]),
        username=str(required["username"]),
        caption=item.caption or "",
        published_at=published_at,
        language=(item.provider_language or "und")[:5],
        market=request.market,
        metrics=metrics,
        hashtags=hashtags,
        sound_id=music.id,
        sound_title=music.title,
        provider=provider,
        retrieved_at=retrieved_at,
        freshness_at=retrieved_at,
        confidence=0.85 if not missing_fields else 0.6,
        raw_reference=raw_reference,
        missing_fields=sorted(set(missing_fields)),
        creator_display_name=author.display_name,
        creator_profile_url=author.profile_url,
        creator_followers=author.followers,
        creator_verified=author.verified,
        creator_account_region=item.account_region,
        sound_author=music.author,
        sound_original=music.original,
        hashtag_metadata=hashtag_metadata,
        duration_seconds=metadata.duration,
        is_ad=item.is_ad,
        is_pinned=item.is_pinned,
        is_slideshow=item.is_slideshow,
        collection_type=request.collection_type.value,
        discovery_queries=query_values,
        provider_run_id=run_id,
        dataset_id=dataset_id,
        availability_status="available",
        normalizer_version=NORMALIZER_VERSION,
        schema_fingerprint=fingerprint,
    )
