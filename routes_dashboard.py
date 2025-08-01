
from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse
import os
import json

router = APIRouter()

USAGE_FILE = "model_usage_log.json"
MODELS_FILE = "models.json"

@router.get("/dashboard")
async def dashboard_page():
    return FileResponse("dashboard.html")

@router.get("/dashboard/data")
async def dashboard_data():
    if not os.path.exists(USAGE_FILE):
        return JSONResponse({})
    with open(USAGE_FILE, "r") as f:
        usage = json.load(f)
    with open(MODELS_FILE, "r") as f:
        models = json.load(f)["models"]
    for name in usage:
        usage[name]["cost"] = models.get(name, {}).get("cost", 0)
    return JSONResponse(usage)
