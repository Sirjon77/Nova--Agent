import pytest, asyncio, types, json, pathlib
from nova.governance import governance_loop
from nova.governance.niche_manager import ChannelMetrics
from nova.governance.tool_checker import ToolConfig

@pytest.mark.asyncio
async def test_governance_run(tmp_path, monkeypatch):
    cfg = {
        "output_dir": tmp_path,
        "niche":{
            "weights":{"rpm":2,"watch":1.5,"ctr":1,"subs":1},
            "consistency_bonus":5,
            "thresholds":{"retire":25,"watch":40,"promote":65}
        },
        "trends":{"rpm_multiplier":1,"top_n":5},
        "tools":{"cost_threshold":0.002},
    }
    channels = [ChannelMetrics("c",5,2,0.02,5,[5]*7)]
    seeds = ["ai"]
    tools_cfg = [ToolConfig("X","https://x/ping",100,0.0005)]

    async def fake_scan(self,seeds): return [{"keyword":"ai","interest":50,"projected_rpm":40,"scanned_on":"2025-07-03"}]
    async def fake_check(self,tool): return {"tool":"X","latency_ms":50,"status":"ok","score":80}
    monkeypatch.setattr(governance_loop.TrendScanner, "scan", fake_scan)
    monkeypatch.setattr(governance_loop.ToolChecker, "check", fake_check)

    report = await governance_loop.run(cfg, channels, seeds, tools_cfg)
    assert "channels" in report and "trends" in report and "tools" in report
    file_path = pathlib.Path(cfg["output_dir"]) / f"governance_report_{report['timestamp'][:10]}.json"
    assert file_path.exists()
    data = json.loads(file_path.read_text())
    assert data["channels"][0]["channel_id"] == "c"
