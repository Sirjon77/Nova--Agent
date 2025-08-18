import requests

def sync_to_notion(database_id, data, notion_token):
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": database_id},
        "properties": data
    }
    res = requests.post(url, headers=headers, json=payload)
    return res.status_code, res.json()