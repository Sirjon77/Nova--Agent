
import json
import os
import logging

USAGE_FILE = "model_usage_log.json"

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Setup a logger with the given name and level."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Create console handler if it doesn't exist
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

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
