from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol


def utc_now() -> datetime:
    """Return naive UTC for compatibility with existing SQLAlchemy DateTime fields."""

    return datetime.now(UTC).replace(tzinfo=None)


@dataclass
class ProviderVideo:
    id: str
    url: str
    creator_id: str
    username: str
    caption: str
    published_at: datetime
    language: str
    market: str
    metrics: dict[str, int | None]
    hashtags: list[str] = field(default_factory=list)
    sound_id: str | None = None
    sound_title: str | None = None
    provider: str = "unknown"
    retrieved_at: datetime = field(default_factory=utc_now)
    freshness_at: datetime = field(default_factory=utc_now)
    confidence: float = 0.8
    raw_reference: str = ""
    missing_fields: list[str] = field(default_factory=list)
    creator_display_name: str | None = None
    creator_profile_url: str | None = None
    creator_followers: int | None = None
    creator_verified: bool | None = None
    creator_account_region: str | None = None
    sound_author: str | None = None
    sound_original: bool | None = None
    hashtag_metadata: list[dict[str, str | None]] = field(default_factory=list)
    duration_seconds: int | None = None
    is_ad: bool | None = None
    is_pinned: bool | None = None
    is_slideshow: bool | None = None
    collection_type: str | None = None
    discovery_queries: list[str] = field(default_factory=list)
    provider_run_id: str | None = None
    dataset_id: str | None = None
    availability_status: str = "available"
    normalizer_version: str = "unknown"
    schema_fingerprint: str | None = None


class Provider(Protocol):
    def discover_videos(self)->list[ProviderVideo]: ...
    def get_video_metrics(self,video_ids:list[str])->dict[str,dict[str,int|None]]: ...
    def refresh_video_urls(self,video_urls:list[str])->list[ProviderVideo]: ...
    def get_creator_profile(self,creator_id:str)->dict: ...
    def get_creator_recent_videos(self,creator_id:str)->list[ProviderVideo]: ...
    def discover_hashtags(self)->list[dict]: ...
    def discover_sounds(self)->list[dict]: ...
    def get_sound_videos(self,sound_id:str)->list[ProviderVideo]: ...
    def health_check(self)->dict: ...
