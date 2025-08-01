
def parse_email(raw_email_text):
    return {
        "subject": "Mock Subject",
        "sender": "sender@example.com",
        "body": raw_email_text[:100] + "..."
    }
