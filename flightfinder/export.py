"""N8N workflow export for flight monitoring."""

import json


class N8NExporter:
    """Generate n8n workflow JSON for flight monitoring."""

    def generate_workflow(
        self,
        name: str,
        command: str,
        alert_threshold: float | None = None,
        schedule: str = "0 9 * * *",
    ) -> str:
        """Generate n8n workflow JSON.

        Args:
            name: Workflow name
            command: CLI command to execute
            alert_threshold: Price threshold for alerts (optional)
            schedule: Cron schedule (default: daily at 9am)

        Returns:
            JSON string of the n8n workflow
        """
        threshold_code = alert_threshold if alert_threshold else "null"
        workflow = {
            "name": name,
            "nodes": [
                {
                    "parameters": {
                        "rule": {
                            "interval": [
                                {"field": "cronExpression", "expression": schedule}
                            ]
                        }
                    },
                    "id": "schedule",
                    "name": "Schedule Trigger",
                    "type": "n8n-nodes-base.scheduleTrigger",
                    "typeVersion": 1.1,
                    "position": [0, 0],
                },
                {
                    "parameters": {"command": command},
                    "id": "execute",
                    "name": "Run FlightFinder",
                    "type": "n8n-nodes-base.executeCommand",
                    "typeVersion": 1,
                    "position": [220, 0],
                },
                {
                    "parameters": {
                        "jsCode": f"""
const results = JSON.parse($input.first().json.stdout);
const threshold = {threshold_code};

if (threshold && results.length > 0) {{
  const cheapest = results[0];
  if (cheapest.price < threshold) {{
    return [{{ json: {{ alert: true, ...cheapest }} }}];
  }}
}}
return [{{ json: {{ alert: false, results }} }}];
"""
                    },
                    "id": "check",
                    "name": "Check Threshold",
                    "type": "n8n-nodes-base.code",
                    "typeVersion": 2,
                    "position": [440, 0],
                },
            ],
            "connections": {
                "Schedule Trigger": {
                    "main": [
                        [{"node": "Run FlightFinder", "type": "main", "index": 0}]
                    ]
                },
                "Run FlightFinder": {
                    "main": [[{"node": "Check Threshold", "type": "main", "index": 0}]]
                },
            },
        }

        return json.dumps(workflow, indent=2)
