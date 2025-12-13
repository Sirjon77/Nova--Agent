"""
Governance Report Generator

Compiles an enriched governance report including:
- Insight summaries
- Channel recommendations (status + recommendation text)
- New niche suggestions (stubbed; integrate TI subsystem later)
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Any

try:
    # scoring.py at repository root
    from scoring import METRIC_WEIGHTS  # type: ignore
except Exception:
    METRIC_WEIGHTS = {}


def fetch_trending_niches() -> List[Dict[str, Any]]:
    """
    Stub function to fetch high-potential trending niches.
    Returns a list of dict with keys: 'niche', 'source', 'rpm', 'competition', 'rationale'.
    """
    return [
        {
            "niche": "Electric Vehicles",
            "source": "Google Trends",
            "rpm": 15.0,
            "competition": "low",
            "rationale": (
                "Electric Vehicles are surging in search popularity with high monetization potential "
                "(RPM ~$15) and relatively few established channels."
            ),
        }
    ]


def generate_governance_report(recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a structured report (as a dict) from channel recommendations and trend data."""
    report: Dict[str, Any] = {}
    report["date"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")

    promote_list = [rec.get("channel") for rec in recommendations if rec.get("status") == "promote"]
    retire_list = [rec.get("channel") for rec in recommendations if rec.get("status") == "retire"]

    insights: List[str] = []
    if promote_list:
        insights.append(
            f"Channels poised for growth: {', '.join(promote_list)} – showing strong momentum and high performance. "
            "Recommend doubling down on these niches."
        )
    if retire_list:
        insights.append(
            f"Underperforming channels: {', '.join(retire_list)} – falling below performance thresholds. "
            "Consider phasing out or pivoting strategy for these."
        )
    if not promote_list and not retire_list:
        insights.append(
            "Most channels are in a stable range with no immediate extreme actions recommended. Continue monitoring for subtle trend shifts."
        )

    # Additional monetization insight (RPM-weight heuristic)
    for rec in recommendations:
        if rec.get("status") == "watch":
            if "Maintain and watch" in str(rec.get("recommendation")) and METRIC_WEIGHTS.get("RPM", 0) > 0:
                insights.append(
                    f"Monetization opportunity: {rec.get('channel')} has high RPM potential. Even with average growth, "
                    "its niche could yield higher revenue – consider modest investment."
                )
                break

    report["insight_summaries"] = insights
    report["channel_recommendations"] = recommendations

    # Add new niche suggestions (stub)
    report["new_niche_suggestions"] = []
    for niche in fetch_trending_niches():
        report["new_niche_suggestions"].append(
            {
                "niche": niche.get("niche"),
                "source": niche.get("source"),
                "rationale": niche.get("rationale"),
            }
        )

    return report


