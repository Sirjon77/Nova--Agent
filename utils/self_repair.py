"""If a function fails, ask the model for a fix suggestion."""
import traceback
from utils.model_router import chat_completion

def auto_repair(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        tb = traceback.format_exc()
        ask = f"""You are Nova diagnostic AI. The following traceback occurred:
        {tb}
        Suggest a one-line code fix or alternative call."""
        suggestion = chat_completion(ask, temperature=0.0)
        return {"error": str(e), "suggestion": suggestion}
