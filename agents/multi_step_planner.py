"""Simple Plan → Execute chain using reflection prompts."""
import openai, os
from utils.model_router import chat_completion

SYSTEM = """You are a planning sub-agent. 
First PLAN as bullet steps, then DELIVER final answer when finished.""" 

def plan_and_execute(user_goal: str, context: str = "") -> str:
    plan_prompt = f"""{SYSTEM}
    CONTEXT: {context}
    GOAL: {user_goal}
    Begin planning."""
    plan = chat_completion(plan_prompt, temperature=0.3)
    exec_prompt = f"""{SYSTEM}
    PLAN:
    {plan}
    Now execute the plan step by step and give the result."""
    return chat_completion(exec_prompt, temperature=0.3)
