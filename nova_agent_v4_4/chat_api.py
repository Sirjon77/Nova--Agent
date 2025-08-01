"""FastAPI chat endpoint with short‑ and long‑term memory wiring."""
import os, uuid, json
from fastapi import FastAPI, Request, Response, Cookie
from pydantic import BaseModel
from memory_router import assemble_prompt, store_short
from openai import OpenAI
client = OpenAI()

app = FastAPI()

class ChatBody(BaseModel):
    message: str

@app.post("/api/chat")
async def chat(body: ChatBody, session_id: str | None = Cookie(default=None)):
    # 1 ▪ Session cookie
    if not session_id:
        session_id = str(uuid.uuid4())
        set_cookie = True
    else:
        set_cookie = False

    user_msg = body.message
    prompt = assemble_prompt(session_id, user_msg)

    # Call the LLM
    completion = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": prompt}],
    )

    assistant_reply = completion.choices[0].message.content
    store_short(session_id, user_msg, assistant_reply)

    resp = {"reply": assistant_reply}
    response = Response(content=json.dumps(resp), media_type="application/json")
    if set_cookie:
        response.set_cookie("session_id", session_id, httponly=True, samesite="Lax")
    return response
