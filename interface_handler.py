from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from nova.phases.pipeline import run_phases
import os

router = APIRouter(prefix="/interface", tags=["interface"])
WS_SECRET = os.getenv("WS_SECRET_KEY", "changeme")

@router.post("/chat")
async def chat_endpoint(payload: dict):
    message = payload.get("message", "")
    return {"reply": run_phases(message)}

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    token = ws.query_params.get("token")
    if token != WS_SECRET:
        await ws.close(code=1008)
        return
    await ws.accept()
    try:
        while True:
            data = await ws.receive_text()
            # Stream phases back to client
            for phase, out in run_phases(data, stream=True):
                await ws.send_json({"type": phase, "data": out})
    except WebSocketDisconnect:
        pass
