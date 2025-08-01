"""Negotiation Coach Module.

This module contains a basic framework for constructing negotiation
playbooks.  The ``NegotiationCoach`` class provides methods to build
a negotiation framework tailored to a given industry and target
audience.  Each framework includes a preparation checklist,
communication strategies and a closing plan.  This skeleton can be
expanded with advanced negotiation tactics, case studies or NLP
techniques to optimise deal outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class NegotiationFramework:
    """Represents a negotiation strategy blueprint."""

    industry: str
    target_audience: str
    preparation: List[str]
    communication: List[str]
    closing: List[str]


class NegotiationCoach:
    """Constructs negotiation mastery frameworks."""

    def create_framework(self, industry: str, audience: str) -> NegotiationFramework:
        """Build a high-level negotiation plan for the given context.

        Args:
            industry: The industry or niche involved.
            audience: The target audience for the negotiation.

        Returns:
            A ``NegotiationFramework`` instance.
        """
        preparation = [
            "Research the counterpart's goals and constraints",
            "Define your BATNA (Best Alternative To a Negotiated Agreement)",
            "Gather data on market rates and precedents",
        ]
        communication = [
            "Open with rapport-building questions",
            "Use open-ended questions to uncover needs",
            "Stay assertive yet collaborative",
        ]
        closing = [
            "Summarise agreed points and confirm understanding",
            "Propose a fair and mutually beneficial solution",
            "Document the agreement and outline next steps",
        ]
        return NegotiationFramework(
            industry=industry,
            target_audience=audience,
            preparation=preparation,
            communication=communication,
            closing=closing,
        )
