from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # ESPN
    espn_s2: str = ""
    espn_swid: str = ""
    espn_league_id: int = 77367779

    # Anthropic
    anthropic_api_key: str = ""

    # Database
    database_url: str = "sqlite+aiosqlite:///./draftwarroom.db"

    # App
    app_env: str = "development"
    secret_key: str = "change-me-in-production"

    # NFL season (use most recent completed/active season)
    nfl_season: int = 2024

    model_config = {
        "env_file": os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        "env_file_encoding": "utf-8",
    }

    @property
    def db_path(self) -> str:
        """Extract the file path from the database URL."""
        return self.database_url.replace("sqlite+aiosqlite:///", "")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
