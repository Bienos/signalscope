from __future__ import annotations

from pydantic import BaseModel, Field, SecretStr, field_validator

from app.config import Settings


class ApifyProviderSettings(BaseModel):
    """Backend-only configuration for the Apify provider.

    Actor names intentionally use the public ``owner/name`` format accepted by
    the official Apify client. Provider output may still contain internal Actor
    IDs; those values are treated as provenance and never as configuration.
    """

    enabled: bool = False
    token: SecretStr = SecretStr("")
    api_base: str = "https://api.apify.com"
    primary_actor_id: str = "apidojo/tiktok-scraper-api"
    fallback_actor_id: str = "clockworks/tiktok-scraper"
    enable_fallback: bool = True
    # Apify currently rejects per-run maximum charge ceilings below USD 0.50.
    fallback_max_total_charge_usd: float = Field(default=0.5, ge=0.5)
    discover_actor_id: str = "clockworks/tiktok-discover-scraper"
    enable_discover: bool = False
    max_results_per_query: int = Field(default=50, ge=1, le=1000)
    max_items_per_run: int = Field(default=500, ge=1, le=100_000)
    max_total_charge_usd: float = Field(default=5.0, ge=0.5)
    max_retries: int = Field(default=3, ge=0, le=10)
    default_market: str = "GB"
    default_language: str = "en"
    supported_markets: tuple[str, ...] = ("GB", "PL")
    run_timeout_seconds: int = Field(default=600, ge=30, le=86_400)
    request_timeout_seconds: int = Field(default=60, ge=5, le=300)
    monthly_budget_usd: float = Field(default=50.0, gt=0)
    raw_payload_retention_days: int = Field(default=14, ge=0, le=365)
    toy_discovery_enabled: bool = True
    toy_monitoring_percentage: int = Field(default=10, ge=0, le=100)
    provider_mode: str = "demo"

    @field_validator("api_base")
    @classmethod
    def canonical_api_base(cls, value: str) -> str:
        # The official client expects the service root and appends /v2 itself.
        return value.strip().rstrip("/").removesuffix("/v2")

    @field_validator("primary_actor_id", "fallback_actor_id", "discover_actor_id")
    @classmethod
    def canonical_actor_name(cls, value: str) -> str:
        actor = value.strip().replace("~", "/")
        if actor.count("/") != 1 or any(not part for part in actor.split("/")):
            raise ValueError("Apify Actor IDs must use owner/name format")
        return actor

    @field_validator("primary_actor_id")
    @classmethod
    def supported_primary_actor(cls, value: str) -> str:
        if value not in {
            "apidojo/tiktok-scraper-api",
            "clockworks/tiktok-scraper",
        }:
            raise ValueError("Primary Actor must use a supported SignalScope contract")
        return value

    @field_validator("fallback_actor_id")
    @classmethod
    def supported_fallback_actor(cls, value: str) -> str:
        if value != "clockworks/tiktok-scraper":
            raise ValueError("Fallback Actor must be clockworks/tiktok-scraper")
        return value

    @field_validator("default_market")
    @classmethod
    def uppercase_market(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("default_language")
    @classmethod
    def clean_language(cls, value: str) -> str:
        language = value.strip().lower()
        if not language:
            raise ValueError("APIFY_DEFAULT_LANGUAGE must not be empty")
        return language

    @field_validator("supported_markets")
    @classmethod
    def clean_markets(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        markets = tuple(dict.fromkeys(item.strip().upper() for item in value if item.strip()))
        if not markets:
            raise ValueError("At least one APIFY_SUPPORTED_MARKETS value is required")
        return markets

    @field_validator("provider_mode")
    @classmethod
    def valid_provider_mode(cls, value: str) -> str:
        mode = value.strip().lower()
        if mode not in {"demo", "live"}:
            raise ValueError("TOY_PROVIDER_MODE must be demo or live")
        return mode

    @property
    def live_enabled(self) -> bool:
        return self.enabled and self.provider_mode == "live" and bool(self.token.get_secret_value())

    def configuration_issues(self, *, require_discovery: bool = False) -> list[str]:
        issues: list[str] = []
        if not self.enabled:
            issues.append("APIFY_ENABLED is false")
        if self.provider_mode != "live":
            issues.append("TOY_PROVIDER_MODE is not live")
        if not self.token.get_secret_value():
            issues.append("APIFY_TOKEN is not configured")
        if self.default_market not in self.supported_markets:
            issues.append("APIFY_DEFAULT_MARKET is not included in APIFY_SUPPORTED_MARKETS")
        if require_discovery and not self.toy_discovery_enabled:
            issues.append("TOY_DISCOVERY_ENABLED is false")
        return issues

    @classmethod
    def from_app_settings(cls, value: Settings) -> "ApifyProviderSettings":
        supported = tuple(
            item.strip().upper() for item in value.apify_supported_markets.split(",") if item.strip()
        )
        legacy_market = (value.apify_proxy_country_code or "").strip().upper()
        default_market = (
            legacy_market if legacy_market and legacy_market != "NONE" else value.apify_default_market
        )
        return cls(
            enabled=value.apify_enabled,
            token=value.apify_token,
            api_base=value.apify_api_base_url or value.apify_api_base,
            primary_actor_id=value.apify_actor_id or value.apify_primary_actor_id,
            fallback_actor_id=value.apify_fallback_actor_id,
            enable_fallback=value.apify_enable_fallback,
            fallback_max_total_charge_usd=value.apify_fallback_max_total_charge_usd,
            discover_actor_id=value.apify_discover_actor_id,
            enable_discover=value.apify_enable_discover,
            max_results_per_query=value.apify_results_per_page
            or value.apify_max_results_per_query,
            max_items_per_run=value.apify_max_items or value.apify_max_items_per_run,
            max_total_charge_usd=value.apify_max_total_charge_usd,
            max_retries=value.apify_max_retries,
            default_market=default_market,
            default_language=value.apify_default_language,
            supported_markets=supported,
            run_timeout_seconds=value.apify_timeout_seconds or value.apify_run_timeout_seconds,
            request_timeout_seconds=value.apify_request_timeout_seconds,
            monthly_budget_usd=value.apify_monthly_budget_usd,
            raw_payload_retention_days=value.apify_raw_payload_retention_days,
            toy_discovery_enabled=value.toy_discovery_enabled,
            toy_monitoring_percentage=value.toy_monitoring_percentage,
            provider_mode=value.toy_provider_mode,
        )
