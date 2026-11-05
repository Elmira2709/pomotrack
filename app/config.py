from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str 
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

@lru_cache
def get_settings():
    return Settings()   