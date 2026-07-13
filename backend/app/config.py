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
    apify_actor_id:str="clockworks~tiktok-scraper"
    apify_api_base_url:str="https://api.apify.com"
    apify_search_queries:str="children's toys,STEM toys,sensory toys,collectible toys,construction toys,plush toys,dolls and action figures,outdoor toys,parent toy reviews,gift ideas for kids"
    apify_hashtags:str="toys,stemtoys,sensorytoys,collectibletoys,constructiontoys,plushtoys,dolls,actionfigures,outdoortoys,toyreview"
    apify_profiles:str=""
    apify_post_urls:str=""
    apify_results_per_page:int=25
    apify_max_items:int=100
    apify_max_total_charge_usd:float=2.0
    apify_timeout_seconds:int=180
    apify_proxy_country_code:str="None"
    retention_username_days:int=365
    retention_content_days:int=180

@lru_cache
def settings()->Settings: return Settings()
