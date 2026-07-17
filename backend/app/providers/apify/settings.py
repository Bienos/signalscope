from __future__ import annotations

from pydantic import BaseModel, Field, SecretStr, field_validator

from app.config import Settings


class ApifyProviderSettings(BaseModel):
    enabled: bool = False
    token: SecretStr = SecretStr("")
    api_base: str = "https://api.apify.com/v2"
    discovery_actor_id: str = "clockworks~tiktok-scraper"
    profile_actor_id: str = "clockworks~tiktok-profile-scraper"
    profile_enrichment_enabled: bool = False
    max_results_per_query: int = Field(default=50, ge=1, le=1000)
    default_market: str = "GB"
    supported_markets: tuple[str, ...] = ("GB", "PL")
    run_timeout_seconds: int = Field(default=900, ge=30, le=86_400)
    request_timeout_seconds: int = Field(default=60, ge=5, le=300)
    monthly_budget_usd: float = Field(default=50.0, gt=0)
    raw_payload_retention_days: int = Field(default=14, ge=0, le=365)
    toy_discovery_enabled: bool = True
    toy_monitoring_percentage: int = Field(default=10, ge=0, le=100)
    provider_mode: str = "demo"

    @field_validator("api_base")
    @classmethod
    def canonical_api_base(cls, value: str) -> str:
        base = value.strip().rstrip("/")
        if not base.endswith("/v2"):
            base = f"{base}/v2"
        return base

    @field_validator("default_market")
    @classmethod
    def uppercase_market(cls, value: str) -> str:
        return value.strip().upper()

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
            discovery_actor_id=value.apify_actor_id or value.apify_discovery_actor_id,
            profile_actor_id=value.apify_profile_actor_id,
            profile_enrichment_enabled=value.apify_profile_enrichment_enabled,
            max_results_per_query=value.apify_results_per_page
            or value.apify_max_results_per_query,
            default_market=default_market,
            supported_markets=supported,
            run_timeout_seconds=value.apify_timeout_seconds or value.apify_run_timeout_seconds,
            request_timeout_seconds=value.apify_request_timeout_seconds,
            monthly_budget_usd=value.apify_monthly_budget_usd,
            raw_payload_retention_days=value.apify_raw_payload_retention_days,
            toy_discovery_enabled=value.toy_discovery_enabled,
            toy_monitoring_percentage=value.toy_monitoring_percentage,
            provider_mode=value.toy_provider_mode,
        )
