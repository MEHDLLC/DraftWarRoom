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

    # NFL season
    nfl_season: int = 2026

    # ESPN write API (unofficial): when False, /lineup/apply always dry-runs —
    # it builds and logs the transaction payload but never sends it to ESPN.
    espn_write_enabled: bool = False

    # One-shot remote trigger: when True, startup applies the recommended
    # lineup once (after the bootstrap data refresh), subject to the
    # espn_write_enabled gate above. UNSET THIS after use — leaving it on
    # re-applies the lineup on every restart.
    apply_lineup_on_startup: bool = False

    _env_path: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    model_config = {
        "env_file": _env_path if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")) else None,
        "env_file_encoding": "utf-8",
    }

    @property
    def db_path(self) -> str:
        """Extract the file path from the database URL."""
        return self.database_url.replace("sqlite+aiosqlite:///", "")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
