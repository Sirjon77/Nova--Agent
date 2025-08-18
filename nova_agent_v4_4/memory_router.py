"""Glue code for short‑term (Redis) and long‑term (Weaviate/Chroma) memory."""
from .chat_buffer import get_short, store_short
from .vector_store import retrieve_relevant

def assemble_prompt(session_id: str, user_msg: str) -> str:
    snippets = retrieve_relevant(session_id, user_msg)
    history = get_short(session_id)
    return (
        "SYSTEM: You are a helpful support bot.\n"
        + "".join(snippets)
        + "".join(history)
        + f"USER: {user_msg}\nASSISTANT:"
    )

__all__ = ["assemble_prompt", "store_short"]
