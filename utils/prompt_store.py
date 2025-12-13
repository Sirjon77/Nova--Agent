"""Load prompts from YAML or JSON files stored in /prompts.

Usage:
    from utils.prompt_store import get_prompt
    prompt = get_prompt("example_prompt")
"""
import os
import json
import yaml
CACHE = {}

PROMPT_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")

def _load(name: str):
    path_yaml = os.path.join(PROMPT_DIR, f"{name}.yml")
    path_json = os.path.join(PROMPT_DIR, f"{name}.json")
    if os.path.exists(path_yaml):
        with open(path_yaml, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    if os.path.exists(path_json):
        with open(path_json, "r", encoding="utf-8") as f:
            return json.load(f)
    raise FileNotFoundError(f"Prompt {name} not found")

def get_prompt(name: str):
    if name not in CACHE:
        CACHE[name] = _load(name)
    return CACHE[name]
