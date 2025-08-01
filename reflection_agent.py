import os
import json
from datetime import datetime
from sentence_transformers import SentenceTransformer
import weaviate

REFLECTION_LOG = "reflection_log.json"

client = weaviate.Client(
    url=os.getenv("WEAVIATE_URL"),
    auth_client_secret=weaviate.AuthApiKey(api_key=os.getenv("WEAVIATE_API_KEY")),
    additional_headers={"X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")}
)

embedder = SentenceTransformer("all-MiniLM-L6-v2")

def reflect_on_loop(memory_data, rpm_data):
    reflection = {
        "timestamp": datetime.now().isoformat(),
        "rpm_trend": analyze_rpm(rpm_data),
        "memory_findings": summarize_memory(memory_data),
        "suggested_changes": []
    }

    if reflection["rpm_trend"] == "declining":
        reflection["suggested_changes"].append("Rotate avatars")
        reflection["suggested_changes"].append("Inject new hook prompts")

    save_reflection(reflection)
    return reflection

def analyze_rpm(rpm_data):
    if rpm_data and len(rpm_data) >= 2:
        if rpm_data[-1] < rpm_data[-2]:
            return "declining"
        elif rpm_data[-1] > rpm_data[-2]:
            return "rising"
    return "stable"

def summarize_memory(memory_data):
    if not memory_data:
        return "No memory data found."
    return f"{len(memory_data)} memory records accessed."

def save_reflection(reflection):
    if os.path.exists(REFLECTION_LOG):
        with open(REFLECTION_LOG, "r") as f:
            log = json.load(f)
    else:
        log = []

    log.append(reflection)

    with open(REFLECTION_LOG, "w") as f:
        json.dump(log, f, indent=2)

    # Save to Weaviate
    vector = embedder.encode(reflection["memory_findings"])
    client.data_object.create({
        "summary": reflection["memory_findings"],
        "rpm_trend": reflection["rpm_trend"],
        "suggestions": reflection["suggested_changes"],
        "timestamp": reflection["timestamp"]
    }, class_name="Reflections", vector=vector)