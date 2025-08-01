import os, requests, json

NOTION_TOKEN = os.getenv("NOTION_API_TOKEN")
NOTION_PARENT = os.getenv("NOTION_PARENT_PAGE_ID")  # page or database ID

def export_to_notion(title: str, content: str):
    if not NOTION_TOKEN or not NOTION_PARENT:
        return False
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    data = {
        "parent": {"page_id": NOTION_PARENT},
        "properties": {"title": [{"text": {"content": title}}]},
        "children": [{"object": "block", "type": "paragraph",
                      "paragraph": {"rich_text": [{"text": {"content": content}}]}}]
    }
    requests.post("https://api.notion.com/v1/pages", headers=headers, data=json.dumps(data))
    return True
