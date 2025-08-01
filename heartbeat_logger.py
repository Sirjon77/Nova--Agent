
import smtplib
from email.message import EmailMessage

def send_heartbeat(subject, body, to="jonathanstuart2177@gmail.com"):
    msg = EmailMessage()
    msg["From"] = to
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(to, "your_app_password_here")  # Replace with real app password
        smtp.send_message(msg)

# Example use
if __name__ == "__main__":
    send_heartbeat("✅ Nova Agent Loop Success", "All modules passed and synced.")
