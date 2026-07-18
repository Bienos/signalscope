from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Iterable
from urllib.parse import quote, urlparse


class ActorContract(StrEnum):
    CLOCKWORKS = "clockworks"
    API_DOJO = "apidojo"


class CollectionType(StrEnum):
    KEYWORD = "keyword_discovery"
    HASHTAG = "hashtag_discovery"
    PROFILE = "profile_discovery"
    PROFILE_ENRICHMENT = "profile_enrichment"
    DIRECT_REFRESH = "direct_video_refresh"
    DISCOVER_EXPANSION = "discover_expansion"


class SearchDateRange(StrEnum):
    ALL_TIME = "ALL_TIME"
    PAST_24_HOURS = "PAST_24_HOURS"
    PAST_WEEK = "PAST_WEEK"
    PAST_MONTH = "PAST_MONTH"
    LAST_3_MONTHS = "LAST_3_MONTHS"
    LAST_6_MONTHS = "LAST_6_MONTHS"


@dataclass(frozen=True)
class ActorRequest:
    actor_id: str
    collection_type: CollectionType
    market: str
    result_limit_per_source: int
    maximum_result_count: int
    source_values: tuple[str, ...]
    payload: dict[str, Any]
    paid_input_features: tuple[str, ...] = ()
    language: str = "en"
    contract: ActorContract = ActorContract.CLOCKWORKS
    date_range: SearchDateRange | None = None


MEDIA_DOWNLOAD_INPUTS = (
    "shouldDownloadVideos",
    "shouldDownloadCovers",
    "shouldDownloadSlideshowImages",
    "shouldDownloadAvatars",
    "shouldDownloadMusicCovers",
)
PROFILE_MEDIA_DOWNLOAD_INPUTS = (
    "shouldDownloadVideos",
    "shouldDownloadCovers",
    "shouldDownloadSlideshowImages",
    "shouldDownloadAvatars",
)
COMMENT_COLLECTION_INPUTS = (
    "commentsPerPost",
    "topLevelCommentsPerPost",
    "maxRepliesPerComment",
)
FOLLOW_LIST_INPUTS = (
    "maxFollowersPerProfile",
    "maxFollowingPerProfile",
)
RELATED_EXPANSION_INPUTS = (
    "scrapeRelatedVideos",
    "scrapeRelatedSearchWords",
)


PRIMARY_SAFETY_INPUTS: dict[str, Any] = {
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
}


# The optional profile Actor accepts a smaller schema than the primary Actor.
# Send every supported safety control explicitly, and omit unsupported names
# rather than relying on an Actor to ignore unknown input fields.
PROFILE_SAFETY_INPUTS: dict[str, Any] = {
    "maxFollowersPerProfile": 0,
    "maxFollowingPerProfile": 0,
    "commentsPerPost": 0,
    "topLevelCommentsPerPost": 0,
    "maxRepliesPerComment": 0,
    "shouldDownloadVideos": False,
    "shouldDownloadCovers": False,
    "shouldDownloadSlideshowImages": False,
    "shouldDownloadAvatars": False,
    "downloadSubtitlesOptions": "NEVER_DOWNLOAD_SUBTITLES",
}

# The Discover Actor has a deliberately smaller documented input contract. Do
# not send primary-Actor controls it does not advertise.
DISCOVER_SAFETY_INPUTS: dict[str, Any] = {
    "shouldDownloadVideos": False,
    "shouldDownloadCovers": False,
    "shouldDownloadSlideshowImages": False,
    "downloadSubtitlesOptions": "NEVER_DOWNLOAD_SUBTITLES",
}

API_DOJO_ALLOWED_INPUTS = {
    "startUrls",
    "keywords",
    "sortType",
    "location",
    "dateRange",
    "maxItems",
    "includeSearchKeywords",
}

API_DOJO_DATE_RANGES = {
    SearchDateRange.ALL_TIME: "ALL_TIME",
    SearchDateRange.PAST_24_HOURS: "YESTERDAY",
    SearchDateRange.PAST_WEEK: "THIS_WEEK",
    SearchDateRange.PAST_MONTH: "THIS_MONTH",
    SearchDateRange.LAST_3_MONTHS: "LAST_3_MONTHS",
    SearchDateRange.LAST_6_MONTHS: "LAST_6_MONTHS",
}


def _clean(values: Iterable[str], *, prefix: str = "") -> tuple[str, ...]:
    cleaned = tuple(
        dict.fromkeys(value.strip().removeprefix(prefix) for value in values if value.strip())
    )
    if not cleaned:
        raise ValueError("At least one discovery value is required")
    return cleaned


def _market(value: str, supported_markets: Iterable[str]) -> str:
    market = value.strip().upper()
    supported = {item.strip().upper() for item in supported_markets}
    if market not in supported:
        raise ValueError(f"Unsupported collection market: {market}")
    return market


def _limit(value: int, maximum: int) -> int:
    if value < 1 or value > maximum:
        raise ValueError(f"Result limit must be between 1 and {maximum}")
    return value


def _primary_payload(*, limit: int, market: str) -> dict[str, Any]:
    return {
        **PRIMARY_SAFETY_INPUTS,
        "resultsPerPage": limit,
        "proxyCountryCode": market,
    }


def build_keyword_request(
    *,
    actor_id: str,
    keywords: Iterable[str],
    market: str,
    supported_markets: Iterable[str],
    result_limit: int,
    maximum_per_query: int,
    date_range: SearchDateRange = SearchDateRange.PAST_WEEK,
    language: str = "en",
    contract: ActorContract = ActorContract.CLOCKWORKS,
) -> ActorRequest:
    values = _clean(keywords)
    selected_market = _market(market, supported_markets)
    limit = _limit(result_limit, maximum_per_query)
    maximum_result_count = len(values) * limit
    if contract == ActorContract.API_DOJO:
        payload = {
            "keywords": list(values),
            "sortType": "DATE_POSTED",
            "location": selected_market,
            "dateRange": API_DOJO_DATE_RANGES[date_range],
            "maxItems": maximum_result_count,
            "includeSearchKeywords": True,
        }
        paid_features = ("sortType", "dateRange")
    else:
        payload = {
            **_primary_payload(limit=limit, market=selected_market),
            "searchQueries": list(values),
            "searchSection": "/video",
            "videoSearchSorting": "LATEST",
            "videoSearchDateFilter": date_range.value,
        }
        paid_features = ("videoSearchSorting", "videoSearchDateFilter")
    return ActorRequest(
        actor_id=actor_id,
        collection_type=CollectionType.KEYWORD,
        market=selected_market,
        result_limit_per_source=limit,
        maximum_result_count=maximum_result_count,
        source_values=values,
        payload=payload,
        paid_input_features=paid_features,
        language=language,
        contract=contract,
        date_range=date_range,
    )


def build_hashtag_request(
    *,
    actor_id: str,
    hashtags: Iterable[str],
    market: str,
    supported_markets: Iterable[str],
    result_limit: int,
    maximum_per_query: int,
    language: str = "en",
    contract: ActorContract = ActorContract.CLOCKWORKS,
) -> ActorRequest:
    values = _clean(hashtags, prefix="#")
    selected_market = _market(market, supported_markets)
    limit = _limit(result_limit, maximum_per_query)
    maximum_result_count = len(values) * limit
    if contract == ActorContract.API_DOJO:
        payload = {
            "startUrls": [
                f"https://www.tiktok.com/tag/{quote(value, safe='')}" for value in values
            ],
            "location": selected_market,
            "maxItems": maximum_result_count,
        }
    else:
        payload = {
            **_primary_payload(limit=limit, market=selected_market),
            "hashtags": list(values),
        }
    return ActorRequest(
        actor_id=actor_id,
        collection_type=CollectionType.HASHTAG,
        market=selected_market,
        result_limit_per_source=limit,
        maximum_result_count=maximum_result_count,
        source_values=values,
        payload=payload,
        language=language,
        contract=contract,
    )


def build_profile_request(
    *,
    actor_id: str,
    profiles: Iterable[str],
    market: str,
    supported_markets: Iterable[str],
    result_limit: int,
    maximum_per_query: int,
    enrichment: bool = False,
    language: str = "en",
    contract: ActorContract = ActorContract.CLOCKWORKS,
) -> ActorRequest:
    values = _clean(profiles, prefix="@")
    selected_market = _market(market, supported_markets)
    limit = _limit(result_limit, maximum_per_query)
    maximum_result_count = len(values) * limit
    if contract == ActorContract.API_DOJO:
        if enrichment:
            raise ValueError("API Dojo uses its primary Actor for profile collection")
        payload = {
            "startUrls": [
                f"https://www.tiktok.com/@{quote(value, safe='')}" for value in values
            ],
            "location": selected_market,
            "maxItems": maximum_result_count,
        }
    else:
        safety = PROFILE_SAFETY_INPUTS if enrichment else PRIMARY_SAFETY_INPUTS
        payload = {
            **safety,
            "profiles": list(values),
            "profileScrapeSections": ["videos"],
            "profileSorting": "latest",
            "excludePinnedPosts": True,
            "resultsPerPage": limit,
        }
        if not enrichment:
            payload["proxyCountryCode"] = selected_market
    collection_type = (
        CollectionType.PROFILE_ENRICHMENT if enrichment else CollectionType.PROFILE
    )
    return ActorRequest(
        actor_id=actor_id,
        collection_type=collection_type,
        market=selected_market,
        result_limit_per_source=limit,
        maximum_result_count=maximum_result_count,
        source_values=values,
        payload=payload,
        language=language,
        contract=contract,
    )


def build_direct_refresh_request(
    *,
    actor_id: str,
    video_urls: Iterable[str],
    market: str,
    supported_markets: Iterable[str],
    maximum_urls: int,
    language: str = "en",
    contract: ActorContract = ActorContract.CLOCKWORKS,
) -> ActorRequest:
    values = _clean(video_urls)
    if len(values) > maximum_urls:
        raise ValueError(f"Direct refresh is limited to {maximum_urls} URLs per run")
    for url in values:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not (
            hostname == "tiktok.com" or hostname.endswith(".tiktok.com")
        ):
            raise ValueError("Direct refresh requires canonical HTTPS TikTok URLs")
        if "/video/" not in parsed.path:
            raise ValueError("Direct refresh requires canonical TikTok video URLs")
    selected_market = _market(market, supported_markets)
    if contract == ActorContract.API_DOJO:
        payload = {
            "startUrls": list(values),
            "location": selected_market,
            "maxItems": len(values),
        }
    else:
        payload = {
            **_primary_payload(limit=1, market=selected_market),
            "postURLs": list(values),
        }
    return ActorRequest(
        actor_id=actor_id,
        collection_type=CollectionType.DIRECT_REFRESH,
        market=selected_market,
        result_limit_per_source=1,
        maximum_result_count=len(values),
        source_values=values,
        payload=payload,
        language=language,
        contract=contract,
    )


def build_discover_request(
    *,
    actor_id: str,
    hashtags: Iterable[str],
    market: str,
    supported_markets: Iterable[str],
    result_limit: int,
    maximum_per_query: int,
    language: str = "en",
) -> ActorRequest:
    """Build the documented hashtag-only TikTok Discover Actor request."""

    values = _clean(hashtags, prefix="#")
    selected_market = _market(market, supported_markets)
    limit = _limit(result_limit, maximum_per_query)
    return ActorRequest(
        actor_id=actor_id,
        collection_type=CollectionType.DISCOVER_EXPANSION,
        market=selected_market,
        result_limit_per_source=limit,
        maximum_result_count=len(values) * limit,
        source_values=values,
        payload={
            **DISCOVER_SAFETY_INPUTS,
            "hashtags": list(values),
            "resultsPerPage": limit,
        },
        language=language,
    )


def safety_assertions(request: ActorRequest) -> dict[str, bool]:
    payload = request.payload
    if request.contract == ActorContract.API_DOJO:
        return {
            "documented_inputs_only": set(payload).issubset(API_DOJO_ALLOWED_INPUTS),
            "custom_code_not_supplied": "customMapFunction" not in payload,
            "media_downloads_disabled": not any(
                key in payload for key in MEDIA_DOWNLOAD_INPUTS
            ),
            "subtitles_and_transcripts_disabled": "subtitleInformation" not in payload,
            "comments_disabled": not any(
                key in payload for key in COMMENT_COLLECTION_INPUTS
            ),
            "follower_lists_disabled": not any(
                key in payload for key in FOLLOW_LIST_INPUTS
            ),
        }
    if request.collection_type == CollectionType.DISCOVER_EXPANSION:
        return {
            "media_downloads_disabled": all(
                payload.get(key) is False
                for key in (
                    "shouldDownloadVideos",
                    "shouldDownloadCovers",
                    "shouldDownloadSlideshowImages",
                )
            ),
            "subtitles_and_transcripts_disabled": payload.get(
                "downloadSubtitlesOptions"
            )
            == "NEVER_DOWNLOAD_SUBTITLES",
            "comments_not_requested": not any(
                key in payload for key in COMMENT_COLLECTION_INPUTS
            ),
            "follower_lists_not_requested": not any(
                key in payload for key in FOLLOW_LIST_INPUTS
            ),
            "unsupported_primary_fields_omitted": not any(
                key in payload
                for key in (
                    "proxyCountryCode",
                    "scrapeAdditionalAuthorMeta",
                    *RELATED_EXPANSION_INPUTS,
                )
            ),
        }
    profile_enrichment = request.collection_type == CollectionType.PROFILE_ENRICHMENT
    media_controls = (
        PROFILE_MEDIA_DOWNLOAD_INPUTS if profile_enrichment else MEDIA_DOWNLOAD_INPUTS
    )
    return {
        # These checks are deliberately fail-closed: an omitted key is not
        # evidence that an Actor default is disabled.
        "media_downloads_disabled": all(
            key in payload and payload[key] is False for key in media_controls
        )
        and (
            "shouldDownloadMusicCovers" not in payload
            if profile_enrichment
            else True
        ),
        "subtitles_and_transcripts_disabled": payload.get("downloadSubtitlesOptions")
        == "NEVER_DOWNLOAD_SUBTITLES",
        "comments_disabled": all(
            key in payload and payload[key] == 0 for key in COMMENT_COLLECTION_INPUTS
        ),
        "follower_lists_disabled": all(
            key in payload and payload[key] == 0 for key in FOLLOW_LIST_INPUTS
        ),
        "additional_author_metadata_disabled": (
            "scrapeAdditionalAuthorMeta" not in payload
            if profile_enrichment
            else "scrapeAdditionalAuthorMeta" in payload
            and payload["scrapeAdditionalAuthorMeta"] is False
        ),
        "related_expansion_disabled": (
            all(key not in payload for key in RELATED_EXPANSION_INPUTS)
            if profile_enrichment
            else all(
                key in payload and payload[key] is False
                for key in RELATED_EXPANSION_INPUTS
            )
        ),
    }
