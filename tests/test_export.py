"""Tests for n8n workflow export."""

import json

import pytest

from flightfinder.export import N8NExporter


class TestN8NExporter:
    """Tests for n8n workflow export."""

    @pytest.fixture
    def exporter(self):
        """Create exporter."""
        return N8NExporter()

    def test_generate_workflow_json(self, exporter):
        """Test generating n8n workflow JSON."""
        workflow = exporter.generate_workflow(
            name="cameroon-march",
            command="flightfinder quick JFK YAO 2025-03-15 2025-03-25 --json",
            alert_threshold=1200.0,
            schedule="0 9 * * *",  # Daily at 9am
        )

        # Should be valid JSON
        data = json.loads(workflow)

        assert data["name"] == "cameroon-march"
        assert "nodes" in data
        assert "connections" in data

    def test_workflow_has_schedule_trigger(self, exporter):
        """Test workflow includes schedule trigger node."""
        workflow = exporter.generate_workflow(
            name="test",
            command="flightfinder quick JFK YAO 2025-03-15",
            schedule="0 9 * * *",
        )

        data = json.loads(workflow)
        node_types = [n["type"] for n in data["nodes"]]

        assert "n8n-nodes-base.scheduleTrigger" in node_types

    def test_workflow_has_execute_command(self, exporter):
        """Test workflow includes execute command node."""
        workflow = exporter.generate_workflow(
            name="test",
            command="flightfinder quick JFK YAO 2025-03-15 --json",
        )

        data = json.loads(workflow)
        node_types = [n["type"] for n in data["nodes"]]

        assert "n8n-nodes-base.executeCommand" in node_types

    def test_workflow_command_is_stored(self, exporter):
        """Test the command is stored in the execute node."""
        cmd = "flightfinder quick JFK YAO 2025-03-15 --json"
        workflow = exporter.generate_workflow(
            name="test",
            command=cmd,
        )

        data = json.loads(workflow)
        execute_node = next(n for n in data["nodes"] if "execute" in n["type"].lower())

        assert execute_node["parameters"]["command"] == cmd

    def test_workflow_default_schedule(self, exporter):
        """Test workflow uses default schedule."""
        workflow = exporter.generate_workflow(
            name="test",
            command="flightfinder quick JFK YAO 2025-03-15",
        )

        data = json.loads(workflow)
        schedule_node = next(
            n for n in data["nodes"] if "scheduleTrigger" in n["type"]
        )

        # Default is daily at 9am
        assert "0 9 * * *" in json.dumps(schedule_node)

    def test_workflow_connections_exist(self, exporter):
        """Test workflow has proper node connections."""
        workflow = exporter.generate_workflow(
            name="test",
            command="flightfinder quick JFK YAO 2025-03-15",
        )

        data = json.loads(workflow)

        assert len(data["connections"]) > 0
