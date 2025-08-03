"""Vision agent placeholder using GPT-4o vision endpoint."""
import base64, requests, os
from utils.model_router import chat_completion

# Use model registry for model resolution
try:
    from nova_core.model_registry import resolve as resolve_model
except ImportError:
    # Fallback function if model registry not available
    def resolve_model(alias: str) -> str:
        return alias

def analyse_image(image_path: str, question: str = "What's in the image?"):
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    prompt = f"""<image>{b64}</image> {question}"""
    
    # Use model registry to resolve model alias
    model = resolve_model("gpt-4o-vision")
    
    return chat_completion(prompt, temperature=0.2, model=model)
