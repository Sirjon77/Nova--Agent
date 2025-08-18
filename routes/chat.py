"""/api/chat ‑‑ Unified endpoint for website widget.

Expects JSON:
    { "session_id": "<uuid>", "message": "Hello there" }

Returns:
    { "session_id": "<same‑uuid>", "response": "<assistant_text>" }
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from models.session import Session
from utils.memory_router import (
    store_short,
    get_short,
    store_long,
    retrieve_relevant,
)
from utils.model_router import chat_completion  # existing util in repo

router = APIRouter()

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    session_id: str
    response: str

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(400, "Empty message")

    # Create or resume session
    session = Session(req.session_id)

    # --- Memory recall ---
    relevant_memories = retrieve_relevant(session.id, req.message)
    short_history = get_short(session.id)

    # Build context
    system_prompt = "You are Nova Website Assistant (memory‑enabled)."
    memory_section = "\n".join(
        ["### MEMORY SNIPPETS ###"] + relevant_memories + ["### END MEMORY ###"]
    ) if relevant_memories else ""
    history_section = "\n".join(short_history)

    prompt = f"""{system_prompt}
    {memory_section}
    {history_section}
    USER: {req.message}
    ASSISTANT:"""

    # --- LLM call ---
    assistant_text = chat_completion(prompt)

    # --- Persist memory ---
    store_short(session.id, "USER", req.message)
    store_short(session.id, "ASSISTANT", assistant_text)

    # Heuristic: remember if the user taught us something new
    if len(req.message.split()) > 15 and "remember" in req.message.lower():
        store_long(session.id, req.message)

    session.touch()

    return ChatResponse(session_id=session.id, response=assistant_text)
