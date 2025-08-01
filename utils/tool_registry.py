"""Registry of tools with JSON Schema for GPT function calling."""
import os, json
REGISTRY = {}

def register(tool_name: str, schema: dict, handler):
    REGISTRY[tool_name] = {"schema": schema, "handler": handler}

def get_schema():
    return [v["schema"] for v in REGISTRY.values()]

def call(tool_name: str, args: dict):
    return REGISTRY[tool_name]["handler"](**args)
