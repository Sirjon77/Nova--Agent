"""Wrap external tool calls to capture success/failure feedback."""
import traceback
from utils.memory_router import store_short, store_long

def run_tool_call(session_id: str, tool_fn, *args, **kwargs):
    try:
        result = tool_fn(*args, **kwargs)
        status = "success"
    except Exception as e:
        result = f"{e}\n{traceback.format_exc()}"
        status = "error"
    feedback = f"TOOL_CALL [{tool_fn.__name__}] -> {status}: {str(result)[:400]}"
    store_short(session_id, "SYSTEM", feedback)
    if status == "success":
        store_long(session_id, feedback)
    return result

    # ---- Reflex loop ----
    from utils.openai_wrapper import chat_completion
    def run_tool_call_with_reflex(session_id: str, tool_fn, *args, **kwargs):
        try:
            return run_tool_call(session_id, tool_fn, *args, **kwargs)
        except Exception as e:
            feedback = f"ERROR calling {tool_fn.__name__}: {e}"
            store_short(session_id, "SYSTEM", feedback)
            # ask GPT for fix
            suggestion = chat_completion(
                f"A tool call failed with error:\n{feedback}\nSuggest quick fix.",
                temperature=0
            )
            store_short(session_id, "SYSTEM", "SUGGESTED_FIX: " + suggestion)
            raise
    