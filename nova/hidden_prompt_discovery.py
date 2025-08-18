"""Hidden Prompt Discovery Module.

This module implements a basic framework to generate and rank novel
prompt templates that may be underutilised by other creators.  The
``PromptDiscoverer`` class leverages existing prompt libraries (e.g.,
psychological hooks, trending keywords) and applies simple
combinatorial logic to synthesise new prompt structures.  These can
then be fed into the content generation pipeline or stored in the
prompt vault for later evaluation.

Currently, the implementation focuses on producing a set of prompt
templates given a set of topics and desired outcomes.  In future
versions, it can incorporate machine learning models to identify
underserved niches or high-RPM combinations.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import List


@dataclass
class PromptTemplate:
    """Represents a generic prompt template."""

    structure: str
    description: str
    tags: List[str]


class PromptDiscoverer:
    """Generates hidden or novel prompt structures from seeds."""

    def __init__(self) -> None:
        # Base components for building prompts.  This can be extended
        # with trending topics, psych hooks or domain-specific keywords.
        self.openers = [
            "Act like a {role} with expertise in {domain} and",
            "Pretend you are {role}, specialising in {domain}, and",
            "Imagine being a {role} famous for {domain};",
        ]
        self.instructions = [
            "create a {outcome} roadmap",
            "design a {outcome} blueprint",
            "craft a {outcome} strategy",
            "outline a {outcome} system",
        ]
        self.closers = [
            "for someone in {niche}.",
            "tailored to {niche} audiences.",
            "that maximises engagement in {niche}.",
        ]

    def discover_prompts(
        self,
        roles: List[str],
        domains: List[str],
        outcomes: List[str],
        niches: List[str],
        limit: int = 15,
    ) -> List[PromptTemplate]:
        """Generate combinations of prompt structures.

        Args:
            roles: A list of expert roles (e.g., 'growth hacker').
            domains: A list of domains or industries (e.g., 'AI marketing').
            outcomes: Desired deliverables (e.g., 'profit machine').
            niches: Target niches or industries.
            limit: Maximum number of prompts to return.

        Returns:
            A list of ``PromptTemplate`` objects.
        """
        templates: List[PromptTemplate] = []
        combinations = list(
            itertools.product(self.openers, self.instructions, self.closers)
        )
        for opener, instr, closer in combinations:
            for role in roles:
                for domain in domains:
                    for outcome in outcomes:
                        for niche in niches:
                            text = f"{opener.format(role=role, domain=domain)} {instr.format(outcome=outcome)} {closer.format(niche=niche)}"
                            desc = (
                                f"Prompt for a {role} in {domain} to deliver a {outcome} for {niche}."
                            )
                            tags = [role, domain, outcome, niche]
                            templates.append(PromptTemplate(text, desc, tags))
                            if len(templates) >= limit:
                                return templates
        return templates
