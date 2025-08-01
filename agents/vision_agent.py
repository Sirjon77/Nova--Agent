"""Vision agent placeholder using GPT-4o vision endpoint."""
import base64, requests, os
from utils.model_router import chat_completion

def analyse_image(image_path: str, question: str = "What’s in the image?"):
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    prompt = f"""<image>{b64}</image> {question}"""
    return chat_completion(prompt, temperature=0.2, model="gpt-4o-vision")
