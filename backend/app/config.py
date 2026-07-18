from functools import lru_cache
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config=SettingsConfigDict(env_file=".env", extra="ignore")
    database_url:str="sqlite:///./radar.db"
    app_secret:str="local-development-secret-change-me"
    app_timezone:str="Europe/Warsaw"
    provider_type:str="mock"
    viral_view_threshold:int=1_000_000
    min_high_performance_avs:int=70
    min_high_performance_views:int=250_000
    min_emerging_growth:int=5_000
    max_emerging_anomaly:int=40
    emerging_max_age_hours:int=72
    expected_freshness_hours:int=8
    email_backend:str="file"
    report_recipients:str=""
    provider_base_url:str=""
    provider_auth_header:str="Authorization"
    provider_auth_token:str=""
    provider_field_mapping:dict[str,str]=Field(default_factory=dict)
    apify_enabled:bool=False
    apify_token:SecretStr=SecretStr("")
    apify_api_base:str="https://api.apify.com/v2"
    apify_primary_actor_id:str="apidojo/tiktok-scraper-api"
    apify_fallback_actor_id:str="clockworks/tiktok-scraper"
    apify_enable_fallback:bool=True
    apify_fallback_max_total_charge_usd:float=0.5
    apify_discover_actor_id:str="clockworks/tiktok-discover-scraper"
    apify_enable_discover:bool=False
    apify_max_results_per_query:int=50
    apify_max_items_per_run:int=500
    apify_max_total_charge_usd:float=5.0
    apify_max_retries:int=3
    apify_default_market:str="GB"
    apify_default_language:str="en"
    apify_supported_markets:str="GB,PL"
    apify_run_timeout_seconds:int=600
    apify_request_timeout_seconds:int=60
    apify_monthly_budget_usd:float=50.0
    apify_raw_payload_retention_days:int=14
    toy_discovery_enabled:bool=True
    toy_monitoring_percentage:int=10
    toy_provider_mode:str="demo"
    # Empty values use app/domain/toys/seeds.json. Non-empty environment values
    # are deliberate run-specific overrides, not a second copy of the taxonomy.
    apify_search_queries:str=""
    apify_hashtags:str=""
    apify_profiles:str=""
    apify_post_urls:str=""
    # Legacy environment names are read for local upgrade compatibility but are
    # intentionally absent from .env.example. New deployments use the fields above.
    apify_actor_id:str|None=None
    apify_api_base_url:str|None=None
    apify_results_per_page:int|None=None
    apify_max_items:int|None=None
    apify_timeout_seconds:int|None=None
    apify_proxy_country_code:str|None=None
    retention_username_days:int=365
    retention_content_days:int=180

@lru_cache
def settings()->Settings: return Settings()
