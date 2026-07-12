from functools import lru_cache
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
    provider_auth_token:str=""
    retention_username_days:int=365
    retention_content_days:int=180

@lru_cache
def settings()->Settings: return Settings()
