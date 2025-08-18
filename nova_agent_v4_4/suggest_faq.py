import os
import smtplib
from redis_client import r

def run_daily():
    for key in r.keys("query:*"):
        count = int(r.get(key))
        if count >= 3:
            q = key.split(":",1)[1]
            message = f"Consider adding to FAQ: {q} (asked {count}× in 24h)."
            send_email("FAQ Suggestion", message)

def send_email(subject: str, body: str):
    to_addr = os.getenv("ADMIN_EMAIL")
    if not to_addr:
        return
    msg = f"Subject: {subject}\n\n{body}"
    with smtplib.SMTP("localhost") as s:
        s.sendmail("nova-agent@example.com", to_addr, msg)
