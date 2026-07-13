from __future__ import annotations

from typing import cast

from app.config import Settings, settings
from app.domain.toys import load_toy_taxonomy

from .apify import ApifyProviderSettings, ApifyTikTokProvider
from .base import Provider
from .generic_rest import GenericRestProvider
from .mock import MockProvider


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def provider_factory(config: Settings | None = None, *, mock_run: int = 0) -> Provider:
    cfg = config or settings()
    provider_type = cfg.provider_type.strip().lower()
    if provider_type == "mock":
        return MockProvider(mock_run)
    if provider_type == "apify":
        apify_settings = ApifyProviderSettings.from_app_settings(cfg)
        taxonomy = load_toy_taxonomy()
        explicit_queries = _split(cfg.apify_search_queries)
        explicit_hashtags = _split(cfg.apify_hashtags)
        taxonomy_queries = [
            term
            for language in sorted(taxonomy.search_terms)
            for term in taxonomy.search_terms[language]
        ]
        return ApifyTikTokProvider(
            settings=apify_settings,
            search_queries=explicit_queries or taxonomy_queries,
            hashtags=explicit_hashtags or list(taxonomy.hashtags),
            profiles=_split(cfg.apify_profiles),
            post_urls=_split(cfg.apify_post_urls),
            max_items=cfg.apify_max_items,
            max_total_charge_usd=cfg.apify_max_total_charge_usd,
        )
    if provider_type == "generic_rest":
        return cast(
            Provider,
            GenericRestProvider(
                cfg.provider_base_url,
                cfg.provider_auth_header,
                cfg.provider_auth_token,
                cfg.provider_field_mapping,
            ),
        )
    raise ValueError(f"Unknown PROVIDER_TYPE: {cfg.provider_type}")
