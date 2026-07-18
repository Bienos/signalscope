from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Iterable, TypedDict

from pydantic import ValidationError

from app.providers.base import ProviderVideo

from .errors import redact_text
from .inputs import ActorContract, ActorRequest
from .schemas import (
    ActorAuthor,
    ActorMusic,
    ActorTikTokItem,
    ActorVideoMetadata,
    ApiDojoChannel,
    ApiDojoSong,
    ApiDojoTikTokItem,
    ApiDojoVideo,
)


NORMALIZER_VERSION = "apify-toy-1.3"


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


def _related_terms(values: list[Any] | None) -> list[str]:
    related: list[str] = []
    for value in values or []:
        if isinstance(value, str) and value.strip():
            related.append(value.strip().removeprefix("#"))
        elif isinstance(value, dict):
            candidate = value.get("name") or value.get("tag") or value.get("title")
            if isinstance(candidate, str) and candidate.strip():
                related.append(candidate.strip().removeprefix("#"))
    return list(dict.fromkeys(related))


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
            item = (
                ApiDojoTikTokItem.model_validate(raw)
                if request.contract == ActorContract.API_DOJO
                else ActorTikTokItem.model_validate(raw)
            )
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
            if isinstance(item, ApiDojoTikTokItem):
                video = _normalize_api_dojo_item(
                    item,
                    request=request,
                    run_id=run_id,
                    dataset_id=dataset_id,
                    retrieved_at=retrieved_at,
                    fingerprint=fingerprint,
                )
            else:
                video = _normalize_item(
                    item,
                    request=request,
                    run_id=run_id,
                    dataset_id=dataset_id,
                    retrieved_at=retrieved_at,
                    fingerprint=fingerprint,
                )
            result.videos.append(video)
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


def _api_dojo_hashtags(values: list[Any] | None) -> tuple[list[str], list[dict[str, str | None]]]:
    names: list[str] = []
    metadata: list[dict[str, str | None]] = []
    for value in values or []:
        provider_id: str | None = None
        name: str | None = None
        title: str | None = None
        if isinstance(value, str):
            name = value
        elif isinstance(value, dict):
            raw_name = value.get("name") or value.get("title")
            raw_id = value.get("id")
            name = raw_name if isinstance(raw_name, str) else None
            provider_id = str(raw_id) if raw_id is not None else None
            raw_title = value.get("title")
            title = raw_title if isinstance(raw_title, str) else None
        if name and name.strip():
            cleaned = name.strip().removeprefix("#")
            names.append(cleaned)
            metadata.append(
                {"provider_id": provider_id, "name": cleaned, "title": title}
            )
    return list(dict.fromkeys(names)), metadata


def _normalize_api_dojo_item(
    item: ApiDojoTikTokItem,
    *,
    request: ActorRequest,
    run_id: str,
    dataset_id: str,
    retrieved_at: datetime,
    fingerprint: str,
) -> ProviderVideo:
    channel = item.channel or ApiDojoChannel()
    required = {
        "provider_video_id": item.id,
        "canonical_url": item.canonical_url,
        "provider_creator_id": channel.id,
        "username": channel.username,
    }
    missing_identity = [name for name, value in required.items() if not value]
    if missing_identity:
        raise ValueError("Missing required identity fields: " + ", ".join(missing_identity))

    missing_fields: list[str] = ["language", "creator_account_region"]
    published_at = item.uploaded_at_formatted
    if published_at is None and item.uploaded_at is not None:
        published_at = datetime.fromtimestamp(item.uploaded_at, tz=timezone.utc)
    if published_at is None:
        published_at = retrieved_at
        missing_fields.append("published_at")
    published_at = _utc_naive(published_at)
    if item.caption is None:
        missing_fields.append("caption")
    if item.hashtags is None:
        missing_fields.append("hashtags")

    metrics: dict[str, int | None] = {
        "views": item.views,
        "likes": item.likes,
        "comments": item.comments,
        "shares": item.shares,
        "saves": item.saves,
        "favourites": item.saves,
    }
    missing_fields.extend(
        name for name in ("views", "likes", "comments", "shares", "saves")
        if metrics[name] is None
    )
    hashtags, hashtag_metadata = _api_dojo_hashtags(item.hashtags)
    song = item.song or ApiDojoSong()
    if song.id is None:
        missing_fields.append("sound_id")
    metadata = item.video or ApiDojoVideo()
    if metadata.duration is None:
        missing_fields.append("duration_seconds")

    query_values = (
        [item.input_source]
        if item.input_source and item.input_source.strip()
        else list(request.source_values)
    )
    provider = f"apify:{request.actor_id}"
    raw_reference = (
        f"apify://{request.actor_id}/runs/{run_id}/datasets/{dataset_id}/video/"
        f"{required['provider_video_id']}"
    )
    return ProviderVideo(
        id=str(required["provider_video_id"]),
        url=str(required["canonical_url"]),
        creator_id=str(required["provider_creator_id"]),
        username=str(required["username"]),
        caption=item.caption or "",
        published_at=published_at,
        language="und",
        market=request.market,
        metrics=metrics,
        hashtags=hashtags,
        sound_id=str(song.id) if song.id is not None else None,
        sound_title=song.title,
        provider=provider,
        retrieved_at=retrieved_at,
        freshness_at=retrieved_at,
        confidence=0.85 if len(missing_fields) <= 2 else 0.6,
        raw_reference=raw_reference,
        missing_fields=sorted(set(missing_fields)),
        creator_display_name=channel.name,
        creator_profile_url=channel.url,
        creator_followers=channel.followers,
        creator_verified=channel.verified,
        creator_account_region=None,
        sound_author=song.artist,
        sound_original=None,
        hashtag_metadata=hashtag_metadata,
        duration_seconds=int(metadata.duration) if metadata.duration is not None else None,
        collection_type=request.collection_type.value,
        discovery_queries=query_values,
        discovery_context={"provider_contract": ActorContract.API_DOJO.value},
        provider_run_id=run_id,
        dataset_id=dataset_id,
        availability_status="available",
        normalizer_version=NORMALIZER_VERSION,
        schema_fingerprint=fingerprint,
    )


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
    discovery_info = item.discovery_info
    seed_tag = discovery_info.tag.removeprefix("#") if discovery_info and discovery_info.tag else None
    related_terms = _related_terms(discovery_info.related_tags if discovery_info else None)
    discovery_context: dict[str, object] = {
        "seed": seed_tag,
        "related_terms": related_terms,
        "discovery_type": discovery_info.discovery_type if discovery_info else None,
    }
    if item.search_hashtag:
        discovery_context["search_hashtag"] = {
            key: item.search_hashtag.get(key) for key in ("name", "views")
        }
    if item.search_music:
        discovery_context["search_music"] = {
            key: item.search_music.get(key) for key in ("musicTag", "videos")
        }
    discovery_context = {
        key: value
        for key, value in discovery_context.items()
        if value not in (None, [], {})
    }
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
        duration_seconds=int(metadata.duration) if metadata.duration is not None else None,
        is_ad=item.is_ad,
        is_pinned=item.is_pinned,
        is_slideshow=item.is_slideshow,
        collection_type=request.collection_type.value,
        discovery_queries=query_values,
        discovery_context=discovery_context,
        provider_run_id=run_id,
        dataset_id=dataset_id,
        availability_status="available",
        normalizer_version=NORMALIZER_VERSION,
        schema_fingerprint=fingerprint,
    )
