from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt, ValidationError

from .base import ProviderVideo

ACTOR_ID = "clockworks~tiktok-scraper"
PROVIDER_NAME = f"apify:{ACTOR_ID}"
METRIC_FIELDS = {
    "views": "playCount",
    "likes": "diggCount",
    "comments": "commentCount",
    "shares": "shareCount",
    "favourites": "collectCount",
}


class ApifyAuthor(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str | None = None
    name: str | None = None
    profile_url: str | None = Field(default=None, alias="profileUrl")


class ApifyMusic(BaseModel):
    model_config = ConfigDict(extra="ignore")

    music_id: str | None = Field(default=None, alias="musicId")
    music_name: str | None = Field(default=None, alias="musicName")
    music_author: str | None = Field(default=None, alias="musicAuthor")
    music_original: bool | None = Field(default=None, alias="musicOriginal")


class ApifyHashtag(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str | None = None
    name: str | None = None
    title: str | None = None


class ApifyTikTokItem(BaseModel):
    """The only place where Clockworks/Apify output field names are accepted."""

    model_config = ConfigDict(extra="ignore")

    id: str | None = None
    text: str | None = None
    text_language: str | None = Field(default=None, alias="textLanguage")
    create_time: int | None = Field(default=None, alias="createTime")
    create_time_iso: datetime | None = Field(default=None, alias="createTimeISO")
    web_video_url: str | None = Field(default=None, alias="webVideoUrl")
    location_created: str | None = Field(default=None, alias="locationCreated")
    author: ApifyAuthor | None = Field(default=None, alias="authorMeta")
    music: ApifyMusic | None = Field(default=None, alias="musicMeta")
    hashtags: list[ApifyHashtag] | None = None
    digg_count: NonNegativeInt | None = Field(default=None, alias="diggCount")
    share_count: NonNegativeInt | None = Field(default=None, alias="shareCount")
    play_count: NonNegativeInt | None = Field(default=None, alias="playCount")
    comment_count: NonNegativeInt | None = Field(default=None, alias="commentCount")
    collect_count: NonNegativeInt | None = Field(default=None, alias="collectCount")
    submitted_video_url: str | None = Field(default=None, alias="submittedVideoUrl")
    search_query: str | None = Field(default=None, alias="searchQuery")
    input_value: str | None = Field(default=None, alias="input")
    error: str | None = None
    error_code: str | None = Field(default=None, alias="errorCode")


class ApifyTikTokProvider:
    """Small, paid-run-capped adapter for the Clockworks TikTok Scraper Actor."""

    def __init__(
        self,
        *,
        token: str,
        enabled: bool = False,
        actor_id: str = ACTOR_ID,
        base_url: str = "https://api.apify.com",
        search_queries: Iterable[str] = (),
        hashtags: Iterable[str] = (),
        profiles: Iterable[str] = (),
        post_urls: Iterable[str] = (),
        results_per_page: int = 25,
        max_items: int = 100,
        max_total_charge_usd: float = 2.0,
        timeout_seconds: int = 180,
        proxy_country_code: str = "None",
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._token = token
        self.enabled = enabled
        self.actor_id = actor_id
        self.base_url = base_url.rstrip("/")
        self.search_queries = self._clean(search_queries)
        self.hashtags = [value.removeprefix("#") for value in self._clean(hashtags)]
        self.profiles = [value.removeprefix("@") for value in self._clean(profiles)]
        self.post_urls = self._clean(post_urls)
        self.results_per_page = max(1, min(results_per_page, 100))
        self.max_items = max(1, max_items)
        self.max_total_charge_usd = max_total_charge_usd
        self.timeout_seconds = max(30, min(timeout_seconds, 300))
        self.proxy_country_code = proxy_country_code or "None"
        self._transport = transport
        self._videos: dict[str, ProviderVideo] = {}
        self.last_run_quality: dict[str, Any] = {}

    @staticmethod
    def _clean(values: Iterable[str]) -> list[str]:
        return list(dict.fromkeys(value.strip() for value in values if value.strip()))

    def _assert_ready(self) -> None:
        if not self.enabled:
            raise RuntimeError("Apify provider is disabled; set APIFY_ENABLED=true explicitly")
        if not self._token:
            raise RuntimeError("APIFY_TOKEN is required when the Apify provider is enabled")
        if self.actor_id != ACTOR_ID:
            raise ValueError(f"This connector only supports {ACTOR_ID}")
        if self.max_total_charge_usd <= 0:
            raise ValueError("APIFY_MAX_TOTAL_CHARGE_USD must be greater than zero")

    def _actor_input(
        self,
        *,
        search_queries: Iterable[str] = (),
        hashtags: Iterable[str] = (),
        profiles: Iterable[str] = (),
        post_urls: Iterable[str] = (),
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "resultsPerPage": self.results_per_page,
            "searchSection": "/video",
            "profileScrapeSections": ["videos"],
            "profileSorting": "latest",
            "scrapeRelatedSearchWords": False,
            "scrapeRelatedVideos": False,
            "scrapeAdditionalAuthorMeta": False,
            "maxFollowersPerProfile": 0,
            "maxFollowingPerProfile": 0,
            "commentsPerPost": 0,
            "topLevelCommentsPerPost": 0,
            "maxRepliesPerComment": 0,
            "shouldDownloadVideos": False,
            "shouldDownloadCovers": False,
            "shouldDownloadSlideshowImages": False,
            "shouldDownloadAvatars": False,
            "shouldDownloadMusicCovers": False,
            "downloadSubtitlesOptions": "NEVER_DOWNLOAD_SUBTITLES",
            "proxyCountryCode": self.proxy_country_code,
        }
        optional = {
            "searchQueries": self._clean(search_queries),
            "hashtags": [value.removeprefix("#") for value in self._clean(hashtags)],
            "profiles": [value.removeprefix("@") for value in self._clean(profiles)],
            "postURLs": self._clean(post_urls),
        }
        payload.update({key: value for key, value in optional.items() if value})
        if not any(key in payload for key in optional):
            raise ValueError("At least one keyword, hashtag, profile, or TikTok video URL is required")
        return payload

    def _run(self, actor_input: dict[str, Any]) -> list[ProviderVideo]:
        self._assert_ready()
        url = f"/v2/actors/{self.actor_id}/run-sync-get-dataset-items"
        params = {
            "timeout": self.timeout_seconds,
            "maxItems": self.max_items,
            "maxTotalChargeUsd": self.max_total_charge_usd,
            "clean": 1,
        }
        headers = {"Authorization": f"Bearer {self._token}", "Accept": "application/json"}
        # Do not retry this paid POST automatically: an ambiguous timeout could duplicate a paid run.
        with httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=self.timeout_seconds + 30,
            transport=self._transport,
        ) as client:
            response = client.post(url, params=params, json=actor_input)
            response.raise_for_status()
            raw_items = response.json()
        if not isinstance(raw_items, list):
            raise ValueError("Apify Actor response must be a JSON list of dataset items")
        videos: list[ProviderVideo] = []
        errors: list[dict[str, str | None]] = []
        invalid = 0
        retrieved_at = datetime.now(timezone.utc).replace(tzinfo=None)
        for raw in raw_items:
            if not isinstance(raw, dict):
                invalid += 1
                continue
            try:
                item = ApifyTikTokItem.model_validate(raw)
            except ValidationError:
                invalid += 1
                continue
            if item.error or item.error_code:
                errors.append({"code": item.error_code, "message": item.error})
                continue
            try:
                video = self._map_item(item, retrieved_at)
            except ValueError:
                invalid += 1
                continue
            videos.append(video)
            self._videos[video.id] = video
        self.last_run_quality = {
            "actor_id": self.actor_id,
            "returned_items": len(raw_items),
            "mapped_videos": len(videos),
            "error_items": errors,
            "invalid_items": invalid,
            "missing_priority_metrics": sum(
                any(field in video.missing_fields for field in METRIC_FIELDS) for video in videos
            ),
        }
        if not videos and (errors or invalid):
            raise ValueError("Apify returned no usable TikTok video items")
        return videos

    def _map_item(self, item: ApifyTikTokItem, retrieved_at: datetime) -> ProviderVideo:
        author = item.author or ApifyAuthor()
        required = {
            "id": item.id,
            "url": item.web_video_url or item.submitted_video_url,
            "creator_id": author.id,
            "username": author.name,
        }
        missing_identity = [key for key, value in required.items() if not value]
        if missing_identity:
            raise ValueError("Missing identity fields: " + ", ".join(missing_identity))
        published_at = item.create_time_iso
        if published_at is None and item.create_time is not None:
            published_at = datetime.fromtimestamp(item.create_time, tz=timezone.utc)
        missing_fields: list[str] = []
        if published_at is None:
            published_at = retrieved_at
            missing_fields.append("published_at")
        if published_at.tzinfo is not None:
            published_at = published_at.astimezone(timezone.utc).replace(tzinfo=None)
        language = item.text_language or "und"
        market = (item.location_created or "ZZ").upper()
        if item.text_language is None:
            missing_fields.append("language")
        if item.location_created is None:
            missing_fields.append("market")
        if item.text is None:
            missing_fields.append("caption")
        if item.hashtags is None:
            missing_fields.append("hashtags")
        metric_values = {
            "views": item.play_count,
            "likes": item.digg_count,
            "comments": item.comment_count,
            "shares": item.share_count,
            "favourites": item.collect_count,
        }
        missing_fields.extend(key for key, value in metric_values.items() if value is None)
        hashtags = [tag.name.removeprefix("#") for tag in item.hashtags or [] if tag.name]
        music = item.music or ApifyMusic()
        if not music.music_id:
            missing_fields.append("sound_id")
        raw_reference = f"apify://{self.actor_id}/video/{required['id']}"
        return ProviderVideo(
            id=str(required["id"]),
            url=str(required["url"]),
            creator_id=str(required["creator_id"]),
            username=str(required["username"]),
            caption=item.text or "",
            published_at=published_at,
            language=language[:5],
            market=market[:5],
            metrics=metric_values,
            hashtags=hashtags,
            sound_id=music.music_id,
            sound_title=music.music_name,
            provider=PROVIDER_NAME,
            retrieved_at=retrieved_at,
            freshness_at=retrieved_at,
            confidence=0.8 if not missing_fields else 0.6,
            raw_reference=raw_reference,
            missing_fields=sorted(set(missing_fields)),
        )

    def discover_videos(self) -> list[ProviderVideo]:
        return self._run(
            self._actor_input(
                search_queries=self.search_queries,
                hashtags=self.hashtags,
                profiles=self.profiles,
                post_urls=self.post_urls,
            )
        )

    def refresh_video_urls(self, video_urls: list[str]) -> list[ProviderVideo]:
        return self._run(self._actor_input(post_urls=video_urls))

    def get_video_metrics(self, video_ids: list[str]) -> dict[str, dict[str, int | None]]:
        cached = {video_id: self._videos[video_id].metrics for video_id in video_ids if video_id in self._videos}
        unknown = [video_id for video_id in video_ids if video_id not in cached]
        if unknown:
            raise ValueError("Refresh unknown videos by direct TikTok URL before requesting metrics")
        return cached

    def get_creator_profile(self, creator_id: str) -> dict[str, Any]:
        videos = self.get_creator_recent_videos(creator_id)
        return {
            "id": creator_id,
            "username": videos[0].username if videos else creator_id.removeprefix("@"),
            "provider": PROVIDER_NAME,
            "recent_video_count": len(videos),
        }

    def get_creator_recent_videos(self, creator_id: str) -> list[ProviderVideo]:
        return self._run(self._actor_input(profiles=[creator_id]))

    def discover_hashtags(self) -> list[dict[str, Any]]:
        observed: dict[str, int] = {}
        for video in self._videos.values():
            for hashtag in video.hashtags:
                observed[hashtag] = observed.get(hashtag, 0) + 1
        names = list(dict.fromkeys([*self.hashtags, *observed]))
        return [
            {"name": name, "observed_videos": observed.get(name), "provider": PROVIDER_NAME}
            for name in names
        ]

    def discover_sounds(self) -> list[dict[str, Any]]:
        sounds: dict[str, dict[str, Any]] = {}
        for video in self._videos.values():
            if video.sound_id:
                sounds.setdefault(
                    video.sound_id,
                    {"id": video.sound_id, "title": video.sound_title, "provider": PROVIDER_NAME},
                )
        return list(sounds.values())

    def get_sound_videos(self, sound_id: str) -> list[ProviderVideo]:
        return [video for video in self._videos.values() if video.sound_id == sound_id]

    def health_check(self) -> dict[str, Any]:
        return {
            "ok": self.enabled and bool(self._token),
            "provider": PROVIDER_NAME,
            "enabled": self.enabled,
            "token_configured": bool(self._token),
            "actor_id": self.actor_id,
            "network_check": "not run",
        }
