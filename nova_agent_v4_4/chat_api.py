"""FastAPI chat endpoint with short‑ and long‑term memory wiring."""
import os, uuid, json
from fastapi import APIRouter, Request, Response, Cookie
from pydantic import BaseModel
from .memory_router import assemble_prompt, store_short

# Use the new OpenAI client wrapper that forces model translation
try:
    from nova.services.openai_client import chat_completion
except ImportError:
    # Fallback to direct OpenAI call if wrapper not available
    from openai import OpenAI
    client = OpenAI()
    def chat_completion(messages, model=None, **kwargs):
        return client.chat.completions.create(messages=messages, **kwargs)

router = APIRouter(prefix="/api/v4", tags=["chat"])

class ChatBody(BaseModel):
    message: str

@router.post("/chat")
async def chat(body: ChatBody, session_id: str | None = Cookie(default=None)):
    # 1 ▪ Session cookie
    if not session_id:
        session_id = str(uuid.uuid4())
        set_cookie = True
    else:
        set_cookie = False

    user_msg = body.message
    prompt = assemble_prompt(session_id, user_msg)

    # Use the wrapper that automatically translates model aliases
    model_alias = os.getenv("OPENAI_MODEL", "gpt-4o")

    # Call the LLM using the wrapper
    completion = chat_completion(
        messages=[{"role": "user", "content": prompt}],
        model=model_alias,  # Will be automatically translated to official model ID
    )

    assistant_reply = completion.choices[0].message.content
    store_short(session_id, user_msg, assistant_reply)

    resp = {"reply": assistant_reply}
    response = Response(content=json.dumps(resp), media_type="application/json")
    if set_cookie:
        response.set_cookie("session_id", session_id, httponly=True, samesite="Lax")
    return response
