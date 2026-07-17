from __future__ import annotations

from dataclasses import asdict, dataclass

from .settings import ApifyProviderSettings


@dataclass(frozen=True)
class ProviderCapabilities:
    provider: str
    discovery_actor: str
    profile_actor: str
    keyword_discovery: bool
    hashtag_discovery: bool
    selected_profile_discovery: bool
    direct_video_refresh: bool
    profile_enrichment: bool
    comments: bool
    transcripts: bool
    follower_lists: bool
    media_downloads: bool
    audience_geography: bool
    complete_platform_coverage: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def provider_capabilities(settings: ApifyProviderSettings) -> ProviderCapabilities:
    return ProviderCapabilities(
        provider="apify",
        discovery_actor=settings.discovery_actor_id,
        profile_actor=settings.profile_actor_id,
        keyword_discovery=True,
        hashtag_discovery=True,
        selected_profile_discovery=True,
        direct_video_refresh=True,
        profile_enrichment=settings.profile_enrichment_enabled,
        comments=False,
        transcripts=False,
        follower_lists=False,
        media_downloads=False,
        audience_geography=False,
        complete_platform_coverage=False,
    )
