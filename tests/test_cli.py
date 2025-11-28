"""Tests for CLI commands."""

from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

from flightfinder.cli import main, quick, search, update_routes


class TestCLI:
    """Tests for CLI entry points."""

    def test_main_group(self):
        """Test main CLI group runs."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Find the cheapest flights" in result.output

    def test_version(self):
        """Test version flag works."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestQuickCommand:
    """Tests for quick search command."""

    def test_quick_no_api_key(self):
        """Test quick command shows error without API key."""
        runner = CliRunner()
        with patch("flightfinder.cli.get_config") as mock_config:
            mock_config.return_value.serpapi_key = None
            result = runner.invoke(quick, ["JFK", "YAO", "2025-03-15", "2025-03-25"])
            assert "API key" in result.output or "SERPAPI_KEY" in result.output

    def test_quick_with_api_key(self):
        """Test quick command executes search with API key."""
        runner = CliRunner()
        with (
            patch("flightfinder.cli.get_config") as mock_config,
            patch("flightfinder.cli.SerpAPIClient"),
            patch("flightfinder.cli.SearchOrchestrator") as mock_orch_cls,
        ):
            mock_config.return_value.serpapi_key = "test-key"
            mock_orch = mock_orch_cls.return_value
            mock_orch.search = AsyncMock(return_value=[])

            result = runner.invoke(quick, ["JFK", "YAO", "2025-03-15", "2025-03-25"])
            assert result.exit_code == 0
            assert "Searching" in result.output or "No flights" in result.output

    def test_quick_multiple_origins(self):
        """Test quick command with multiple origins."""
        runner = CliRunner()
        with (
            patch("flightfinder.cli.get_config") as mock_config,
            patch("flightfinder.cli.SerpAPIClient"),
            patch("flightfinder.cli.SearchOrchestrator") as mock_orch_cls,
        ):
            mock_config.return_value.serpapi_key = "test-key"
            mock_orch = mock_orch_cls.return_value
            mock_orch.search = AsyncMock(return_value=[])

            result = runner.invoke(
                quick, ["JFK,EWR,IAD", "YAO", "2025-03-15", "2025-03-25"]
            )
            assert result.exit_code == 0
            # Should search 3 origins
            assert "Searching 3 origins" in result.output


class TestSearchCommand:
    """Tests for interactive search command."""

    def test_search_no_api_key(self):
        """Test search command shows error without API key."""
        runner = CliRunner()
        with patch("flightfinder.cli.get_config") as mock_config:
            mock_config.return_value.serpapi_key = None
            # Provide minimal input to interactive prompts
            result = runner.invoke(
                search,
                input="JFK\nYAO\nskip\n2025-03-15\n0\nany\nany\n"
                "2025-03-25\nany\nany\neconomy\nnone\n45m\nany\nany\nnone\nn\n",
            )
            assert "API key" in result.output or "SERPAPI_KEY" in result.output


class TestUpdateRoutesCommand:
    """Tests for update-routes command."""

    def test_update_routes_placeholder(self):
        """Test update-routes command runs."""
        runner = CliRunner()
        result = runner.invoke(update_routes)
        assert result.exit_code == 0
        assert "not yet implemented" in result.output or "Route" in result.output
