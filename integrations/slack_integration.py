import os
import requests
import json

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")

def notify(message: str):
    if not SLACK_WEBHOOK:
        return False
    payload = {"text": message}
    requests.post(SLACK_WEBHOOK, data=json.dumps(payload))
    return True
