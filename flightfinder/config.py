"""Configuration loading for FlightFinder."""

import os
from dataclasses import dataclass, field
from pathlib import Path

_config_instance: "Config | None" = None


@dataclass
class Config:
    """Application configuration."""

    serpapi_key: str | None = field(default=None)
    database_path: Path = field(
        default_factory=lambda: Path.home() / ".local/share/flightfinder/flights.db"
    )
    cache_ttl_seconds: int = 21600  # 6 hours
    api_delay_ms: int = 200
    max_retries: int = 3

    def __post_init__(self):
        """Load values from environment."""
        if self.serpapi_key is None:
            self.serpapi_key = os.environ.get("FLIGHTFINDER_SERPAPI_KEY")


def get_config() -> Config:
    """Get the global config instance (singleton)."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
