
from fastapi import FastAPI
from realtime import router as realtime_router
import uvicorn

app = FastAPI()

app.include_router(realtime_router)

@app.get("/status")
def read_status():
    return {
        "status": "Nova Agent v2.5 running",
        "loop": "heartbeat active",
        "version": "2.5"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

from backend.model_api import model_api
app.register_blueprint(model_api)


from fastapi import FastAPI
from realtime import router as realtime_router
from pathlib import Path
import json, os

app = FastAPI()

app.include_router(realtime_router)

MODEL_CONFIG_PATH = Path(__file__).resolve().parent / "config" / "model_tiers.json"

@app.get("/api/current-model-tiers")
async def current_model_tiers():
    if MODEL_CONFIG_PATH.exists():
        return json.loads(MODEL_CONFIG_PATH.read_text())
    return {}