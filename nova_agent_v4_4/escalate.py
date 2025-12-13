import os
import requests

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")

def escalate(session_id: str, transcript: list[str]):
    if not SLACK_WEBHOOK:
        return
    payload = {"text": f"New escalation (session {session_id}):\n```\n" + "".join(transcript) + "\n```"}
    requests.post(SLACK_WEBHOOK, json=payload, timeout=5)
