import requests

def push_to_convertkit(api_key, form_id, email):
    url = f"https://api.convertkit.com/v3/forms/{form_id}/subscribe"
    payload = {
        "api_key": api_key,
        "email": email
    }
    res = requests.post(url, json=payload)
    return res.status_code, res.json()