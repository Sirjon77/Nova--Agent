import math

from scoring import compute_channel_scores, classify_channel, METRIC_WEIGHTS, THRESHOLDS


def test_compute_channel_scores_basic():
    # Sample channel data
    channels = [
        {"name": "ChannelA", "RPM": 10, "growth": 0.05, "engagement": 0.6},  # higher RPM
        {"name": "ChannelB", "RPM": 5, "growth": 0.10, "engagement": 0.4},   # higher growth
    ]
    scores = compute_channel_scores(channels)
    assert set(scores.keys()) == {"ChannelA", "ChannelB"}
    # Both channels have different strengths; ensure score reflects weights:
    # If RPM weight > growth weight, ChannelA should score higher than ChannelB.
    if METRIC_WEIGHTS.get("RPM", 0) > METRIC_WEIGHTS.get("growth", 0):
        assert scores["ChannelA"] > scores["ChannelB"]
    else:
        assert scores["ChannelB"] > scores["ChannelA"]


def test_score_normalization_zero_variance():
    # If all channels have identical metrics, Z-scores should be 0 and composite scores equal.
    channels = [
        {"name": "Chan1", "RPM": 5, "growth": 0.1, "engagement": 0.5},
        {"name": "Chan2", "RPM": 5, "growth": 0.1, "engagement": 0.5},
    ]
    scores = compute_channel_scores(channels)
    # All metrics same, so each channel score should end up 0 (or equal since no differences)
    assert math.isclose(scores["Chan1"], scores["Chan2"], rel_tol=1e-6)
    assert math.isclose(scores["Chan1"], 0.0, rel_tol=1e-6)


def test_classify_channel_thresholds():
    # Test that classify_channel respects the configured thresholds
    high = float(THRESHOLDS["promote"]) + 0.5
    low = float(THRESHOLDS["retire"]) - 0.5
    mid = (float(THRESHOLDS["promote"]) + float(THRESHOLDS["retire"])) / 2.0
    assert classify_channel(high) == "promote"
    assert classify_channel(low) == "retire"
    assert classify_channel(mid) == "watch"


