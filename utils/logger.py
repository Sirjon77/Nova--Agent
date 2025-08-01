
import json
import os

USAGE_FILE = "model_usage_log.json"

def log_model_usage(model, tokens_used):
    if not os.path.exists(USAGE_FILE):
        usage = {}
    else:
        with open(USAGE_FILE, "r") as f:
            usage = json.load(f)
    if model not in usage:
        usage[model] = {"tokens": 0, "calls": 0}
    usage[model]["tokens"] += tokens_used
    usage[model]["calls"] += 1
    with open(USAGE_FILE, "w") as f:
        json.dump(usage, f, indent=2)
