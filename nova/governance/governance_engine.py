"""
Governance engine with policy recommendations (Sprint 01).

- Computes composite scores via scoring.py (Z-score normalization + weights)
- Classifies channels and generates concrete recommendations
- Supports optional safe auto-actions when enabled in config
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from scoring import compute_channel_scores, classify_channel, METRIC_WEIGHTS, THRESHOLDS  # type: ignore


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("governance")


class GovernanceEngine:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # Expect same schema as governance_config.yaml example
        self.auto_actions_enabled = bool(config.get("governance", {}).get("auto_actions", False))
        self.recommendations: List[Dict[str, Any]] = []
        self.actions_executed: List[str] = []

    def analyze_channels(self, channels_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run scoring and policy evaluation on given channels data."""
        scores = compute_channel_scores(channels_data)
        logger.info("Computed scores for %d channels.", len(scores))
        self.recommendations = []

        for channel in channels_data:
            name = channel.get("name")
            score = float(scores.get(name, 0.0))
            status = classify_channel(score)
            rec: Dict[str, Any] = {"channel": name, "score": score, "status": status, "recommendation": None}

            if status == "promote":
                rec["recommendation"] = (
                    f"Double-down on '{name}': This channel is performing excellently. "
                    "Increase posting frequency or invest more resources to capitalize on growth."
                )
            elif status == "retire":
                rec["recommendation"] = (
                    f"Consider retiring or pausing '{name}': Performance is far below threshold. "
                    "It may be resource-intensive with little return; evaluate winding down."
                )
            else:  # watch
                if float(channel.get("growth", 0) or 0) < 0:
                    rec["recommendation"] = (
                        f"Pivot content for '{name}': Growth is negative. Experiment with new content formats "
                        "or topics to rejuvenate this channel."
                    )
                else:
                    rec["recommendation"] = (
                        f"Maintain and watch '{name}': Performance is average/stable. No major changes needed, "
                        "but monitor closely for any trend changes."
                    )

            logger.info(
                "Channel '%s' | Score: %.2f | Status: %s | Rec: %s",
                name,
                score,
                status,
                rec["recommendation"],
            )
            self.recommendations.append(rec)

        return self.recommendations

    def execute_actions(self) -> List[str]:
        """
        Optionally execute recommended actions if auto_actions is enabled.
        Only non-destructive actions are auto-executed by default.
        """
        if not self.auto_actions_enabled:
            return []

        self.actions_executed = []
        for rec in self.recommendations:
            status = rec.get("status")
            name = rec.get("channel")
            if status == "promote":
                logger.info("Auto-executing: Increasing posting frequency for %s.", name)
                # placeholder: schedule a safe cadence boost
                self.actions_executed.append(f"boost_posting:{name}")
            elif status == "retire":
                logger.info(
                    "Auto-action skipped (destructive): %s flagged for retirement (requires human approval).",
                    name,
                )
            else:
                # watch: no action
                pass

        return self.actions_executed


