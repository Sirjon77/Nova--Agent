import json

def load_nova_identity(path="nova_master_prompt_v2.json"):
    try:
        with open(path, "r") as f:
            data = json.load(f)
            print("✅ Nova identity loaded.")
            return data.get("content", "")
    except Exception as e:
        print(f"❌ Failed to load Nova identity: {e}")
        return ""