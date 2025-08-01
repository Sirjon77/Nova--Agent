import weaviate
import os
import json

def embed_memory_to_weaviate(json_path, class_name="NovaMemory"):
    client = weaviate.Client(
        os.getenv("WEAVIATE_ENDPOINT", "http://localhost:8080")
    )

    schema = {
        "class": class_name,
        "properties": [
            {"name": "content", "dataType": ["text"]},
            {"name": "tag", "dataType": ["text"]},
        ],
    }

    if not client.schema.contains(schema):
        client.schema.create_class(schema)

    with open(json_path, "r") as f:
        data = json.load(f)

    for entry in data.get("results", []):
        client.data_object.create(
            data_object={"content": entry, "tag": "loop_log"},
            class_name=class_name
        )

    print("✅ Weaviate memory sync complete.")