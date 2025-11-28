"""Tests for configuration loading."""

import os
from unittest.mock import patch

from flightfinder.config import Config, get_config


class TestConfig:
    """Tests for Config class."""

    def test_config_from_env_var(self):
        """Test loading API key from environment variable."""
        with patch.dict(os.environ, {"FLIGHTFINDER_SERPAPI_KEY": "test-key-123"}):
            config = Config()
            assert config.serpapi_key == "test-key-123"

    def test_config_missing_key_returns_none(self):
        """Test missing API key returns None."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            assert config.serpapi_key is None

    def test_default_database_path(self):
        """Test default database path is set."""
        config = Config()
        assert config.database_path.name == "flights.db"
        assert ".local/share/flightfinder" in str(config.database_path)

    def test_default_cache_ttl(self):
        """Test default cache TTL is 6 hours."""
        config = Config()
        assert config.cache_ttl_seconds == 21600  # 6 hours

    def test_get_config_singleton(self):
        """Test get_config returns same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2
