from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # Database settings
    supabase_url: str
    supabase_key: str
    supabase_service_key: str  # Add this line
    
    # JWT settings
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        env_prefix=''
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()

__all__ = ['settings']
