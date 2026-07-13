from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from typing import Any

from .base import ProviderVideo


# The mock is a labelled, deterministic product fixture. Every template stays
# inside the approved toy/family research scope and contains explicit language
# that the toy classifier can explain.
SIGNAL_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        "category": "sensory toy",
        "mechanism": "unboxing",
        "market": "GB",
        "language": "en",
        "hashtags": ["SensoryToys", "ToyUnboxing"],
        "motion": "steady",
    },
    {
        "category": "plush toy",
        "mechanism": "reaction",
        "market": "GB",
        "language": "en",
        "hashtags": ["Plushies", "ToyTok"],
        "motion": "steady",
    },
    {
        "category": "blind box collectible toy",
        "mechanism": "blind reveal",
        "market": "GB",
        "language": "en",
        "hashtags": ["BlindBox", "CollectibleToys"],
        "motion": "steady",
    },
    {
        "category": "construction toy building set",
        "mechanism": "assembly build with me",
        "market": "GB",
        "language": "en",
        "hashtags": ["ConstructionToys", "PlayIdeas"],
        "motion": "accelerating",
    },
    {
        "category": "STEM toy educational toy",
        "mechanism": "educational demonstration",
        "market": "GB",
        "language": "en",
        "hashtags": ["STEMToys", "EducationalToys"],
        "motion": "breakout",
        "base_views": 120_000,
    },
    {
        "category": "doll accessory",
        "mechanism": "collection reveal",
        "market": "GB",
        "language": "en",
        "hashtags": ["Dolls", "ToyCollection"],
        "motion": "cooling",
    },
    {
        "category": "outdoor toy",
        "mechanism": "product test",
        "market": "GB",
        "language": "en",
        "hashtags": ["OutdoorToys", "ToyReview"],
        "motion": "saturated",
        "base_views": 520_000,
    },
    {
        "category": "board game",
        "mechanism": "parent recommendation",
        "market": "GB",
        "language": "en",
        "hashtags": ["BoardGames", "ParentRecommends"],
        "motion": "viral",
        "base_views": 310_000,
    },
    {
        "category": "prezenty dla dzieci seasonal toy",
        "mechanism": "gift guide",
        "market": "PL",
        "language": "pl",
        "hashtags": ["Zabawki", "PrezentyDlaDzieci"],
        "motion": "breakout",
        "base_views": 105_000,
    },
    {
        "category": "klocki konstrukcyjne construction toy",
        "mechanism": "comparison",
        "market": "PL",
        "language": "pl",
        "hashtags": ["ZabawkiDlaDzieci", "ConstructionToys"],
        "motion": "steady",
    },
    {
        "category": "zabawki sensoryczne sensory toy",
        "mechanism": "recenzja zabawki product test",
        "market": "PL",
        "language": "pl",
        "hashtags": ["ZabawkiSensoryczne", "ToyReview"],
        "motion": "cooling",
    },
    {
        "category": "zabawki kolekcjonerskie collectible toy",
        "mechanism": "rozpakowywanie zabawek unboxing",
        "market": "PL",
        "language": "pl",
        "hashtags": ["CollectibleToys", "ToyUnboxing"],
        "motion": "steady",
    },
)

HASHTAG_FIXTURES: tuple[str, ...] = (
    "ToyTok",
    "ToyReview",
    "ToyUnboxing",
    "SensoryToys",
    "Plushies",
    "BlindBox",
    "CollectibleToys",
    "ConstructionToys",
    "PlayIdeas",
    "STEMToys",
    "EducationalToys",
    "Dolls",
    "ToyCollection",
    "OutdoorToys",
    "BoardGames",
    "ParentRecommends",
    "Zabawki",
    "PrezentyDlaDzieci",
    "ZabawkiDlaDzieci",
    "ZabawkiSensoryczne",
)

_MOTION_INCREMENTS: dict[str, tuple[int, int, int, int]] = {
    "breakout": (0, 25_000, 90_000, 210_000),
    "accelerating": (0, 12_000, 38_000, 82_000),
    "steady": (0, 24_000, 48_000, 72_000),
    "cooling": (0, 52_000, 78_000, 88_000),
    "flat": (0, 2_000, 3_000, 3_500),
    "saturated": (0, 4_000, 8_000, 12_000),
    "viral": (0, 32_000, 64_000, 96_000),
}

# Counts are intentionally uneven so the domain calculation can demonstrate
# every lifecycle honestly: sparse evidence, emerging/accelerating/breakout,
# declining, broad saturated adoption and high-scale viral evidence.
VIDEO_ALLOCATION: tuple[int, ...] = (1, 1, 3, 3, 4, 3, 10, 6, 4, 4, 4, 5)
FIXTURE_VIDEO_COUNT = sum(VIDEO_ALLOCATION)


def _signal_position(index: int) -> tuple[int, int]:
    fixture_index = index % FIXTURE_VIDEO_COUNT
    cycle = index // FIXTURE_VIDEO_COUNT
    offset = 0
    for signal_index, allocated in enumerate(VIDEO_ALLOCATION):
        if fixture_index < offset + allocated:
            return signal_index, fixture_index - offset + cycle * allocated
        offset += allocated
    raise AssertionError("Fixture allocation does not cover the requested index")


class MockProvider:
    """Deterministic synthetic toy intelligence; never accesses TikTok."""

    def __init__(self, run: int = 0):
        self.run = run

    def discover_videos(self, count: int = 48) -> list[ProviderVideo]:
        now = datetime.now(UTC).replace(tzinfo=None)
        output: list[ProviderVideo] = []
        for index in range(count):
            signal_index, template_round = _signal_position(index)
            signal = SIGNAL_TEMPLATES[signal_index]
            if signal["market"] == "GB":
                creator_index = (signal_index * 3 + template_round) % 12
            else:
                creator_index = 12 + ((signal_index - 8) * 2 + template_round) % 8
            rng = random.Random(260711 + index)
            base_views = int(
                signal.get("base_views", 18_000 + signal_index * 14_000)
            ) + template_round * 3_500
            schedule = _MOTION_INCREMENTS[str(signal["motion"])]
            observed_run = min(max(self.run, 0), len(schedule) - 1)
            extra_runs = max(0, self.run - (len(schedule) - 1))
            increment = schedule[observed_run] + extra_runs * max(
                500, schedule[-1] - schedule[-2]
            )
            views = base_views + increment + rng.randrange(500, 2_500)
            share_rate = (
                0.04
                if signal["motion"] == "breakout"
                else 0.024
                if signal["motion"] == "accelerating"
                else 0.009
            )
            missing_fields: list[str] = []
            favourites: int | None = int(
                views * (0.02 if signal["motion"] == "breakout" else 0.013)
            )
            if index % 13 == 12:
                favourites = None
                missing_fields.append("favourites")
            unsafe_prefix = "Choking risk — safety review required. " if index == 0 else ""
            caption = (
                f"{unsafe_prefix}Synthetic demo: {signal['category']} "
                f"{signal['mechanism']}. Independent toy reviewer evidence #{template_round + 1}."
            )
            creator_region = str(signal["market"])
            retrieved_at = now + timedelta(seconds=index)
            output.append(
                ProviderVideo(
                    id=f"mock-{index:04d}",
                    url=(
                        f"https://www.tiktok.com/@toy_researcher_{creator_index:02d}/video/"
                        f"{7400000000000000000 + index}"
                    ),
                    creator_id=f"creator-{creator_index:03d}",
                    username=f"toy_researcher_{creator_index:02d}",
                    caption=caption,
                    published_at=now
                    - timedelta(hours=12 + signal_index * 9 + template_round * 3),
                    language=str(signal["language"]),
                    market=str(signal["market"]),
                    metrics={
                        "views": views,
                        "likes": int(views * 0.076),
                        "comments": int(views * 0.006),
                        "shares": int(views * share_rate),
                        "favourites": favourites,
                    },
                    hashtags=list(signal["hashtags"]),
                    sound_id=f"sound-{signal_index % 8:03d}",
                    sound_title=f"Synthetic observed sound {signal_index % 8 + 1}",
                    provider="mock",
                    retrieved_at=retrieved_at,
                    freshness_at=retrieved_at,
                    raw_reference=f"mock://video/{index}/run/{self.run}",
                    missing_fields=missing_fields,
                    creator_display_name=f"Toy reviewer {creator_index + 1}",
                    creator_profile_url=(
                        f"https://www.tiktok.com/@toy_researcher_{creator_index:02d}"
                    ),
                    creator_followers=8_000 + creator_index * 2_750,
                    creator_verified=creator_index % 7 == 0,
                    creator_account_region=creator_region,
                    sound_author="Synthetic fixture",
                    sound_original=True,
                    hashtag_metadata=[{"name": value} for value in signal["hashtags"]],
                    duration_seconds=18 + signal_index,
                    is_ad=False,
                    is_pinned=False,
                    is_slideshow=signal_index % 4 == 0,
                    collection_type="demo_fixture",
                    discovery_queries=[str(signal["category"])],
                    provider_run_id=f"mock-run-{self.run}",
                    dataset_id="mock-toy-dataset",
                    availability_status="available",
                    normalizer_version="mock-toy-1.0",
                    schema_fingerprint="mock-toy-schema-1",
                )
            )
        return output

    def get_video_metrics(self, ids: list[str]) -> dict[str, dict[str, int | None]]:
        return {video.id: video.metrics for video in self.discover_videos() if video.id in ids}

    def refresh_video_urls(self, video_urls: list[str]) -> list[ProviderVideo]:
        return [video for video in self.discover_videos() if video.url in video_urls]

    def get_creator_profile(self, creator_id: str) -> dict[str, Any]:
        videos = self.get_creator_recent_videos(creator_id)
        first = videos[0] if videos else None
        return {
            "id": creator_id,
            "username": first.username if first else None,
            "display_name": first.creator_display_name if first else None,
            "profile_url": first.creator_profile_url if first else None,
            "followers": first.creator_followers if first else None,
            "account_region": first.creator_account_region if first else None,
            "audience_geography": None,
            "provider": "mock",
        }

    def get_creator_recent_videos(self, creator_id: str) -> list[ProviderVideo]:
        return [video for video in self.discover_videos() if video.creator_id == creator_id]

    def discover_hashtags(self) -> list[dict[str, Any]]:
        videos = self.discover_videos()
        return [
            {
                "name": name,
                "observed_videos": sum(name in video.hashtags for video in videos),
                "unique_creators": len(
                    {video.creator_id for video in videos if name in video.hashtags}
                ),
                "provider": "mock",
                "data_state": "synthetic_demo",
            }
            for name in HASHTAG_FIXTURES
        ]

    def discover_sounds(self) -> list[dict[str, Any]]:
        videos = self.discover_videos()
        return [
            {
                "id": sound_id,
                "title": next(
                    video.sound_title for video in videos if video.sound_id == sound_id
                ),
                "observed_videos": sum(video.sound_id == sound_id for video in videos),
                "provider": "mock",
                "rights_status": "unknown",
                "data_state": "synthetic_demo",
            }
            for sound_id in sorted({video.sound_id for video in videos if video.sound_id})
        ]

    def get_sound_videos(self, sound_id: str) -> list[ProviderVideo]:
        return [video for video in self.discover_videos() if video.sound_id == sound_id]

    def health_check(self) -> dict[str, Any]:
        return {
            "ok": True,
            "provider": "mock",
            "mode": "demo",
            "freshness": "deterministic synthetic fixture",
            "network_check": "not_applicable",
            "complete_platform_coverage": False,
        }
