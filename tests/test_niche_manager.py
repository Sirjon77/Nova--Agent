from nova.governance.niche_manager import NicheManager, ChannelMetrics

def test_flags():
    cfg = {
        "weights": {"rpm":2,"watch":1.5,"ctr":1,"subs":1},
        "consistency_bonus": 5,
        "thresholds": {"retire":25,"watch":40,"promote":65}
    }
    nm = NicheManager(cfg)
    channels = [
        ChannelMetrics("good", 9.0, 5.0, 0.09, 50, [9]*7),
        ChannelMetrics("bad",  0.5, 0.7, 0.01,  1, [1]*7),
    ]
    scored = nm.score_channels(channels)
    flag_map = {c.channel_id: c.flag for c in scored}
    assert flag_map["good"] == "promote"
    assert flag_map["bad"] == "retire"
