from starlette.testclient import TestClient
from nova.api.app import app

def test_ws_echo():
    client = TestClient(app)
    with client.websocket_connect("/ws/events") as ws:
        ws.send_text("hello")
        data = ws.receive_text()
        assert data == "echo: hello"
