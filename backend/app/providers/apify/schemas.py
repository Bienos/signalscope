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

    duration: NonNegativeInt | None = None


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
