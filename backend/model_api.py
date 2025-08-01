
# backend/model_api.py
from flask import Blueprint, request, jsonify

model_api = Blueprint('model_api', __name__)

# Store override in memory (could also persist to file if needed)
active_model_override = {"model": "auto"}

@model_api.route('/api/set-model', methods=['POST'])
def set_model():
    data = request.get_json()
    model = data.get("model", "auto")
    active_model_override["model"] = model
    return jsonify({"status": "ok", "model": model})

@model_api.route('/api/current-model', methods=['GET'])
def get_current_model():
    model = active_model_override.get("model", "auto")
    key_map = {
        "gpt-4o-vision": "OPENAI_KEY_FAST",
        "gpt-4.1": "OPENAI_KEY_STANDARD",
        "gpt-4.1-mini": "OPENAI_KEY_MINI",
        "o3": "OPENAI_KEY_STANDARD",
        "auto": "dynamic (based on task)"
    }
    return jsonify({
        "model": model,
        "key": key_map.get(model, "OPENAI_KEY_STANDARD")
    })
