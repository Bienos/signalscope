"""Backward-compatible import path for the structured Apify provider package."""

from .apify import (
    ACTOR_ID,
    DISCOVERY_ACTOR_ID,
    PROFILE_ACTOR_ID,
    PROVIDER_NAME,
    ApifyTikTokProvider,
)

__all__ = [
    "ACTOR_ID",
    "DISCOVERY_ACTOR_ID",
    "PROFILE_ACTOR_ID",
    "PROVIDER_NAME",
    "ApifyTikTokProvider",
]
