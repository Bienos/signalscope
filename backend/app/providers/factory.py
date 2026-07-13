from __future__ import annotations

from typing import cast

from app.config import Settings, settings

from .apify_tiktok import ApifyTikTokProvider
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
        return ApifyTikTokProvider(
            token=cfg.apify_token.get_secret_value(),
            enabled=cfg.apify_enabled,
            actor_id=cfg.apify_actor_id,
            base_url=cfg.apify_api_base_url,
            search_queries=_split(cfg.apify_search_queries),
            hashtags=_split(cfg.apify_hashtags),
            profiles=_split(cfg.apify_profiles),
            post_urls=_split(cfg.apify_post_urls),
            results_per_page=cfg.apify_results_per_page,
            max_items=cfg.apify_max_items,
            max_total_charge_usd=cfg.apify_max_total_charge_usd,
            timeout_seconds=cfg.apify_timeout_seconds,
            proxy_country_code=cfg.apify_proxy_country_code,
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
