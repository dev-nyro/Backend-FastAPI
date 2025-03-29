from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # Database settings
    supabase_url: str
    supabase_key: str
    supabase_service_key: str
    
    # JWT settings
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Milvus settings
    host: str = "localhost"  # Changed from milvus_host
    port: int = 19530       # Changed from milvus_port
    collection_name: str = "document_chunks"
    embedding_model: str = "all-MiniLM-L6-v2"
    vector_dim: int = 384

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        env_prefix='',
        extra='allow'  # Add this to allow extra fields
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()

__all__ = ['settings']
