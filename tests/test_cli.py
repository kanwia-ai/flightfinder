"""Tests for CLI commands."""

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

    def test_quick_round_trip(self):
        """Test quick command with round trip dates."""
        runner = CliRunner()
        result = runner.invoke(quick, ["JFK", "YAO", "2025-03-15", "2025-03-25"])
        assert result.exit_code == 0
        assert "JFK" in result.output
        assert "YAO" in result.output
        assert "2025-03-15" in result.output
        assert "2025-03-25" in result.output

    def test_quick_one_way(self):
        """Test quick command without return date."""
        runner = CliRunner()
        result = runner.invoke(quick, ["JFK", "YAO", "2025-03-15"])
        assert result.exit_code == 0
        assert "one-way" in result.output


class TestSearchCommand:
    """Tests for interactive search command."""

    def test_search_placeholder(self):
        """Test search command runs."""
        runner = CliRunner()
        result = runner.invoke(search)
        assert result.exit_code == 0
        assert "Interactive search mode" in result.output


class TestUpdateRoutesCommand:
    """Tests for update-routes command."""

    def test_update_routes_placeholder(self):
        """Test update-routes command runs."""
        runner = CliRunner()
        result = runner.invoke(update_routes)
        assert result.exit_code == 0
        assert "Updating routes database" in result.output
