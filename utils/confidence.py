"""Rate confidence of an action proposal (0-1)."""
from utils.model_router import chat_completion

def rate_confidence(action_desc: str, context: str = "") -> float:
    """
    Return a confidence score for the likelihood of an action succeeding.

    This function constructs a prompt requesting a confidence rating between 0 and 1
    for a given action description and optional context, sends it to the language
    model via `chat_completion`, and attempts to parse the first token of the
    response as a float. If parsing fails or any error occurs, a default
    confidence of 0.5 is returned.

    Args:
        action_desc: A description of the proposed action.
        context: Additional context for the action (optional).

    Returns:
        A float between 0 and 1 representing the model's confidence.
    """
    # Compose the prompt as a single multi-line string. Using a triple-quoted
    # string avoids syntax errors due to embedded newlines.
    prompt = (
        f"Rate your confidence (0 to 1) that the following action will succeed in the given context.\n"
        f"ACTION: {action_desc}\n"
        f"CONTEXT: {context}\n"
        "Answer with a single float."
    )
    try:
        resp = chat_completion(prompt, temperature=0.0)
        # Extract the first token and convert to float; fallback to default on error
        return float(resp.strip().split()[0])
    except Exception:
        return 0.5
