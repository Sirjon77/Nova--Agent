from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import json
import asyncio
import time
import pathlib

router = APIRouter()
active_connections = set()

@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # For demo, we echo plus server timestamp
            user_msg = data.get("message", "")
            response = {"user": user_msg, "nova": f"Echo: {user_msg}", "ts": time.time()}
            # send back to sender
            await websocket.send_json(response)
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def log_event_generator(log_file: str):
    path = pathlib.Path(log_file)
    last_size = 0
    while True:
        if path.exists():
            new_size = path.stat().st_size
            if new_size != last_size:
                with path.open("r") as f:
                    f.seek(last_size)
                    for line in f:
                        yield f"data: {json.dumps({'line': line.strip(), 'ts': time.time()})}\n\n"
                last_size = new_size
        await asyncio.sleep(1)

@router.get("/sse/logs")
async def sse_logs():
    return StreamingResponse(log_event_generator("startup_crawl_log.json"), media_type="text/event-stream")