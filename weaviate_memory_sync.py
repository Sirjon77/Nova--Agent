import weaviate
import os
import json

def embed_memory_to_weaviate(json_path, class_name="NovaMemory"):
    # Fix for Weaviate v4: use WeaviateClient instead of Client
    client = weaviate.WeaviateClient(
        connection_params=weaviate.connect.ConnectionParams.from_url(
            os.getenv("WEAVIATE_ENDPOINT", "http://localhost:8080"),
            grpc_port=50051  # Default gRPC port
        )
    )


    # Fix for Weaviate v4: use new API
    try:
        client.collections.get(class_name)
    except:
        # Collection doesn't exist, create it
        client.collections.create(
            name=class_name,
            properties=[
                {"name": "content", "dataType": ["text"]},
                {"name": "tag", "dataType": ["text"]},
            ]
        )

    with open(json_path, "r") as f:
        data = json.load(f)

    for entry in data.get("results", []):
        # Fix for Weaviate v4: use new API
        client.collections.get(class_name).data.insert({
            "content": entry, 
            "tag": "loop_log"
        })

    print("✅ Weaviate memory sync complete.")