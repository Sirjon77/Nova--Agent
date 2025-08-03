"""FastAPI chat endpoint with short‑ and long‑term memory wiring."""
import os, uuid, json
from fastapi import APIRouter, Request, Response, Cookie
from pydantic import BaseModel
from memory_router import assemble_prompt, store_short
from openai import OpenAI

# Use model registry for model resolution
try:
    from nova_core.model_registry import resolve as resolve_model, get_default_model
except ImportError:
    # Fallback function if model registry not available
    def resolve_model(alias: str) -> str:
        return alias
    def get_default_model() -> str:
        return "gpt-4o"

client = OpenAI()

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

    # Use model registry to resolve model alias
    model_alias = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    model = resolve_model(model_alias)

    # Call the LLM
    completion = client.chat.completions.create(
        model=model,  # Now uses resolved official model ID
        messages=[{"role": "user", "content": prompt}],
    )

    assistant_reply = completion.choices[0].message.content
    store_short(session_id, user_msg, assistant_reply)

    resp = {"reply": assistant_reply}
    response = Response(content=json.dumps(resp), media_type="application/json")
    if set_cookie:
        response.set_cookie("session_id", session_id, httponly=True, samesite="Lax")
    return response
