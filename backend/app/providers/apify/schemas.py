from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt


class ActorAuthor(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str | None = None
    name: str | None = None
    display_name: str | None = Field(default=None, alias="nickName")
    profile_url: str | None = Field(default=None, alias="profileUrl")
    followers: NonNegativeInt | None = Field(default=None, alias="fans")
    verified: bool | None = None


class ActorMusic(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str | None = Field(default=None, alias="musicId")
    title: str | None = Field(default=None, alias="musicName")
    author: str | None = Field(default=None, alias="musicAuthor")
    original: bool | None = Field(default=None, alias="musicOriginal")


class ActorHashtag(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str | None = None
    name: str | None = None
    title: str | None = None


class ActorVideoMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")

    # Clockworks currently returns fractional seconds for search results even
    # though direct-video results may contain whole seconds. Accept both at the
    # provider boundary and normalize to the integer domain field later.
    duration: float | None = Field(default=None, ge=0)


class ActorDiscoveryInfo(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    tag: str | None = None
    related_tags: list[Any] | None = Field(default=None, alias="relatedTags")
    discovery_type: str | None = Field(default=None, alias="type")
    url: str | None = None


class ActorTikTokItem(BaseModel):
    """Clockworks output model. Raw provider field aliases stop at this boundary."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str | None = None
    caption: str | None = Field(default=None, alias="text")
    provider_language: str | None = Field(default=None, alias="textLanguage")
    created_timestamp: int | None = Field(default=None, alias="createTime")
    created_at: datetime | None = Field(default=None, alias="createTimeISO")
    canonical_url: str | None = Field(default=None, alias="webVideoUrl")
    submitted_url: str | None = Field(default=None, alias="submittedVideoUrl")
    account_region: str | None = Field(default=None, alias="locationCreated")
    author: ActorAuthor | None = Field(default=None, alias="authorMeta")
    music: ActorMusic | None = Field(default=None, alias="musicMeta")
    video_metadata: ActorVideoMetadata | None = Field(default=None, alias="videoMeta")
    hashtags: list[ActorHashtag] | None = None
    likes: NonNegativeInt | None = Field(default=None, alias="diggCount")
    shares: NonNegativeInt | None = Field(default=None, alias="shareCount")
    views: NonNegativeInt | None = Field(default=None, alias="playCount")
    comments: NonNegativeInt | None = Field(default=None, alias="commentCount")
    saves: NonNegativeInt | None = Field(default=None, alias="collectCount")
    is_ad: bool | None = Field(default=None, alias="isAd")
    is_pinned: bool | None = Field(default=None, alias="isPinned")
    is_slideshow: bool | None = Field(default=None, alias="isSlideshow")
    discovery_query: str | None = Field(default=None, alias="searchQuery")
    input_value: Any | None = Field(default=None, alias="input")
    discovery_info: ActorDiscoveryInfo | None = Field(default=None, alias="discoveryInfo")
    search_hashtag: dict[str, Any] | None = Field(default=None, alias="searchHashtag")
    search_music: dict[str, Any] | None = Field(default=None, alias="searchMusic")
    error_message: str | None = Field(default=None, alias="error")
    error_code: str | None = Field(default=None, alias="errorCode")


class ApiDojoChannel(BaseModel):
    """API Dojo creator fields. Media URLs are intentionally not modelled."""

    model_config = ConfigDict(extra="ignore")

    id: str | int | None = None
    name: str | None = None
    username: str | None = None
    url: str | None = None
    followers: NonNegativeInt | None = None
    verified: bool | None = None


class ApiDojoSong(BaseModel):
    """Selected non-media sound metadata from API Dojo output."""

    model_config = ConfigDict(extra="ignore")

    id: str | int | None = None
    title: str | None = None
    artist: str | None = None
    duration: float | None = Field(default=None, ge=0)


class ApiDojoVideo(BaseModel):
    """Only duration is retained; video, cover and thumbnail URLs are ignored."""

    model_config = ConfigDict(extra="ignore")

    duration: float | None = Field(default=None, ge=0)


class ApiDojoTikTokItem(BaseModel):
    """Documented API Dojo output boundary for normalized TikTok posts."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str | int | None = None
    caption: str | None = Field(default=None, alias="title")
    views: NonNegativeInt | None = None
    likes: NonNegativeInt | None = None
    comments: NonNegativeInt | None = None
    shares: NonNegativeInt | None = None
    saves: NonNegativeInt | None = Field(default=None, alias="bookmarks")
    hashtags: list[Any] | None = None
    channel: ApiDojoChannel | None = None
    uploaded_at: int | None = Field(default=None, alias="uploadedAt")
    uploaded_at_formatted: datetime | None = Field(
        default=None, alias="uploadedAtFormatted"
    )
    video: ApiDojoVideo | None = None
    song: ApiDojoSong | None = None
    canonical_url: str | None = Field(default=None, alias="postPage")
    input_source: str | None = Field(default=None, alias="inputSource")
    error_message: str | None = Field(default=None, alias="error")
    error_code: str | None = Field(default=None, alias="errorCode")


class ActorRun(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str
    actor_id: str | None = Field(default=None, alias="actId")
    status: str
    status_message: str | None = Field(default=None, alias="statusMessage")
    started_at: datetime | None = Field(default=None, alias="startedAt")
    finished_at: datetime | None = Field(default=None, alias="finishedAt")
    dataset_id: str | None = Field(default=None, alias="defaultDatasetId")
    build_id: str | None = Field(default=None, alias="buildId")
    build_number: str | None = Field(default=None, alias="buildNumber")
    usage_total_usd: float | None = Field(default=None, alias="usageTotalUsd")


class ActorRunEnvelope(BaseModel):
    model_config = ConfigDict(extra="ignore")

    data: ActorRun
