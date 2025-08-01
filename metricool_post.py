import requests

def schedule_post_metricool(api_key, account_id, content, publish_time):
    url = f"https://api.metricool.com/v1/accounts/{account_id}/posts"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "content": content,
        "scheduled_time": publish_time
    }
    res = requests.post(url, headers=headers, json=payload)
    return res.status_code, res.json()