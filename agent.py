"""Agent with heartbeat monitoring - reports liveness every 30 seconds.

Demonstrates AXME heartbeat: background thread sends heartbeat to the platform,
which automatically detects healthy/degraded/unreachable states.

Usage:
    export AXME_API_KEY="<agent-key>"
    python agent.py
"""

import os, sys, time, json
sys.stdout.reconfigure(line_buffering=True)
from axme import AxmeClient, AxmeClientConfig

AGENT_ADDRESS = "heartbeat-demo"


def handle_intent(client, intent_id):
    intent_data = client.get_intent(intent_id)
    intent = intent_data.get("intent", intent_data)
    payload = intent.get("payload", {})
    if "parent_payload" in payload:
        payload = payload["parent_payload"]

    task = payload.get("task", "unknown")
    print(f"  Processing: {task}")

    # Simulate work
    time.sleep(2)

    # Report metrics with heartbeat
    client.mesh.report_metric(success=True, latency_ms=2000.0, cost_usd=0.001)

    result = {
        "action": "complete",
        "task": task,
        "status": "done",
        "processed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    client.resume_intent(intent_id, result)
    print(f"  Completed: {task}")


def main():
    api_key = os.environ.get("AXME_API_KEY", "")
    if not api_key:
        print("Error: AXME_API_KEY not set.")
        sys.exit(1)

    client = AxmeClient(AxmeClientConfig(api_key=api_key))

    # Start heartbeat - one line, background thread, 30s interval
    client.mesh.start_heartbeat()
    print("Heartbeat started (30s interval)")
    print(f"Agent listening on {AGENT_ADDRESS}...")
    print("Waiting for intents (Ctrl+C to stop)\n")

    try:
        for delivery in client.listen(AGENT_ADDRESS):
            intent_id = delivery.get("intent_id", "")
            status = delivery.get("status", "")
            if intent_id and status in ("DELIVERED", "CREATED", "IN_PROGRESS"):
                print(f"[{status}] Intent received: {intent_id}")
                try:
                    handle_intent(client, intent_id)
                except Exception as e:
                    client.mesh.report_metric(success=False)
                    print(f"  Error: {e}")
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        client.mesh.stop_heartbeat()
        print("Heartbeat stopped. Agent exited.")


if __name__ == "__main__":
    main()
