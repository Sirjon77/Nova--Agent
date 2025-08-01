import pytest, asyncio
from nova.governance.changelog_watcher import ChangelogWatcher

@pytest.mark.asyncio
async def test_changelog_detect(monkeypatch):
    async def fake_get(self, url):
        class R: status_code = 200
        def json(self): return {'version': '2.0.0'}
        return R()
    import httpx
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    cw = ChangelogWatcher({})
    tools = [{'name': 'X', 'changelog_url': 'https://x/ver', 'current_version': '1.0.0'}]
    out = await cw.scan(tools)
    assert out and out[0]['new_version'] == '2.0.0'
