
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import json
import os

router = APIRouter()
MODULE_STATUS_FILE = "module_status.json"

def load_status():
    if os.path.exists(MODULE_STATUS_FILE):
        with open(MODULE_STATUS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_status(status):
    with open(MODULE_STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)

@router.get("/api/modules")
async def get_module_status():
    return JSONResponse(load_status())

@router.post("/api/modules/toggle")
async def toggle_module(req: Request):
    data = await req.json()
    module = data.get("module")
    enabled = data.get("enabled")
    status = load_status()
    status[module] = enabled
    save_status(status)
    return JSONResponse({"status": "ok", "module": module, "enabled": enabled})
