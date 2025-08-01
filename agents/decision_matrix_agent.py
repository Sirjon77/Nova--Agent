"""Lightweight agent that maps goals to RPA flow names + args."""
import json
from fastapi import FastAPI
from pydantic import BaseModel
from utils.openai_wrapper import chat_completion

app = FastAPI()

class DecisionRequest(BaseModel):
    session_id: str
    goal: str
    context: str = ""

class DecisionResponse(BaseModel):
    flow: str
    payload: dict

SYSTEM = "You are a planner that maps user goals to Zapier/UiPath flow names."

@app.post("/decide", response_model=DecisionResponse)
async def decide(req: DecisionRequest):
    prompt = f"""{SYSTEM}
    GOAL: {req.goal}
    CONTEXT: {req.context}
    Respond with JSON: {{'flow': <flow_name>, 'payload': <dict_args>}}"""
    answer = chat_completion(prompt, temperature=0.1)
    try:
        data = json.loads(answer)
        return DecisionResponse(**data)
    except json.JSONDecodeError:
        return DecisionResponse(flow="NO_FLOW_FOUND", payload={})
