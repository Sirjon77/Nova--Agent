
from fastapi import FastAPI
from realtime import router as realtime_router
from routes.research import router as research_router
from pathlib import Path
import json, os
import uvicorn

app = FastAPI()

app.include_router(realtime_router)
app.include_router(research_router)

MODEL_CONFIG_PATH = Path(__file__).resolve().parent / "config" / "model_tiers.json"

@app.get("/status")
def read_status():
    return {
        "status": "Nova Agent v2.5 running",
        "loop": "heartbeat active",
        "version": "2.5",
        "features": ["autonomous_research", "nlp_intent_detection", "memory_management"]
    }

@app.get("/api/current-model-tiers")
async def current_model_tiers():
    if MODEL_CONFIG_PATH.exists():
        return json.loads(MODEL_CONFIG_PATH.read_text())
    return {}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)