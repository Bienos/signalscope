"""Backward-compatible import path for the structured Apify provider package."""

from .apify import (
    ACTOR_ID,
    API_DOJO_ACTOR_ID,
    CLOCKWORKS_ACTOR_ID,
    DISCOVER_ACTOR_ID,
    DISCOVERY_ACTOR_ID,
    PRIMARY_ACTOR_ID,
    FALLBACK_ACTOR_ID,
    PROFILE_ACTOR_ID,
    PROVIDER_NAME,
    ApifyTikTokProvider,
)

__all__ = [
    "ACTOR_ID",
    "API_DOJO_ACTOR_ID",
    "CLOCKWORKS_ACTOR_ID",
    "FALLBACK_ACTOR_ID",
    "PRIMARY_ACTOR_ID",
    "DISCOVER_ACTOR_ID",
    "DISCOVERY_ACTOR_ID",
    "PROFILE_ACTOR_ID",
    "PROVIDER_NAME",
    "ApifyTikTokProvider",
]
