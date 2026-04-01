"""Initiator - sends a task to the heartbeat-monitored agent and checks health.

Usage:
    export AXME_API_KEY="your-key"
    python initiator.py
"""

from __future__ import annotations
import json, os, sys
from axme import AxmeClient, AxmeClientConfig


def main() -> None:
    api_key = os.environ.get("AXME_API_KEY")
    if not api_key:
        print("Error: AXME_API_KEY required", file=sys.stderr)
        sys.exit(1)

    client = AxmeClient(AxmeClientConfig(api_key=api_key))

    # Check agent health before sending work
    print("Checking agent mesh health...\n")
    mesh_status = client.mesh.list_agents()
    agents = mesh_status.get("agents", [])
    for agent in agents:
        health = agent.get("health_status", "unknown")
        address = agent.get("address", "unknown")
        last_hb = agent.get("last_heartbeat_at", "never")
        print(f"  {address:30s}  health: {health:12s}  last_hb: {last_hb}")
    print()

    # Send a task intent
    print("Sending task to heartbeat-demo agent...")
    intent_id = client.send_intent({
        "intent_type": "intent.ops.process_task.v1",
        "to_agent": "agent://myorg/production/heartbeat-demo",
        "payload": {
            "task": "generate_monthly_report",
            "month": "2026-03",
            "priority": "normal",
        },
    })
    print(f"Intent created: {intent_id}")
    print("Observing lifecycle...\n")

    for event in client.observe(intent_id):
        event_type = event.get("event_type", "unknown")
        data = event.get("data", {})
        print(f"  [{event_type}] {json.dumps(data, indent=2)[:200]}")
        if event_type in ("intent.completed", "intent.failed", "intent.cancelled"):
            break

    final = client.get_intent(intent_id)
    print(f"\nFinal status: {final.get('status')}")

    # Check health again after processing
    print("\nPost-task health check:")
    mesh_status = client.mesh.list_agents()
    for agent in mesh_status.get("agents", []):
        health = agent.get("health_status", "unknown")
        address = agent.get("address", "unknown")
        metrics = agent.get("metrics", {})
        print(f"  {address:30s}  health: {health:12s}  metrics: {json.dumps(metrics)[:100]}")


if __name__ == "__main__":
    main()
