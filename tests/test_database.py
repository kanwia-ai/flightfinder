"""Tests for database connection and setup."""

import sqlite3
from pathlib import Path

import pytest

from flightfinder.db.database import Database


class TestDatabase:
    """Tests for Database class."""

    def test_create_database_in_memory(self):
        """Test creating in-memory database."""
        db = Database(":memory:")
        assert db.connection is not None

    def test_create_tables(self, tmp_path: Path):
        """Test tables are created on init."""
        db_path = tmp_path / "test.db"
        db = Database(str(db_path))

        # Check tables exist
        cursor = db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cursor.fetchall()}

        assert "routes" in tables
        assert "searches" in tables
        assert "prices" in tables

    def test_routes_table_schema(self, tmp_path: Path):
        """Test routes table has correct columns."""
        db_path = tmp_path / "test.db"
        db = Database(str(db_path))

        cursor = db.connection.execute("PRAGMA table_info(routes)")
        columns = {row[1] for row in cursor.fetchall()}

        assert "airline_code" in columns
        assert "origin" in columns
        assert "destination" in columns
        assert "last_updated" in columns

    def test_close_connection(self):
        """Test closing database connection."""
        db = Database(":memory:")
        db.close()
        with pytest.raises(sqlite3.ProgrammingError):
            db.connection.execute("SELECT 1")
