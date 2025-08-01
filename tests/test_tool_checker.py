import pytest, asyncio
from nova.governance.tool_checker import ToolChecker, ToolConfig

@pytest.mark.asyncio
async def test_tool_score_ok(monkeypatch):
    async def fake_get(url):
        class R: status_code = 200
        return R()
    import httpx
    monkeypatch.setattr(httpx.AsyncClient, "get", lambda self, url: fake_get(url))
    tc = ToolChecker({"cost_threshold":0.002})
    result = await tc.check(ToolConfig("X","https://x/ping",100,0.0005))
    assert result["status"] == "ok"
    assert result["score"] > 50
