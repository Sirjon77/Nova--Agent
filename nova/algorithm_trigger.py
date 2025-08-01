"""Algorithm Trigger and Hook Engineering Module.

This module defines utilities for constructing hooks and content
structuring patterns designed to trigger social media algorithms.
These patterns are based on well known retention techniques such as
curiosity gaps, pattern interruptions, and dopamine loops.  The
primary class ``HookEngine`` exposes methods to generate hook
templates for different platforms and evaluate their potential
effectiveness.  This serves as a foundation for A/B testing and
optimising content for maximum engagement.

Note:
    This module intentionally avoids direct API calls or heavy
    dependencies.  It simply defines heuristics and placeholder
    evaluation functions.  When integrated with real data (e.g.,
    watch time analytics), these methods can be expanded to
    dynamically adjust weights or rank hooks.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Dict, Tuple


@dataclass
class HookTemplate:
    """Represents a simple hook template with metadata."""

    text: str
    description: str
    tags: List[str]


class HookEngine:
    """Generates and evaluates hook templates for content videos."""

    def __init__(self) -> None:
        # Predefined library of hook structures.  These can be
        # expanded based on A/B test results and research.
        self.library: List[HookTemplate] = [
            # Classic curiosity and secret revelation
            HookTemplate(
                text="Nobody is talking about this secret ...",
                description="Curiosity gap with a promise of insider information.",
                tags=["curiosity", "secret", "shock"],
            ),
            # Anticipation and payoff hook
            HookTemplate(
                text="Watch until the end to see the surprise twist!",
                description="Creates anticipation with a payoff at the end.",
                tags=["anticipation", "twist", "dopamine"],
            ),
            # Shock and unexpected outcome
            HookTemplate(
                text="You won't believe what happens next ...",
                description="Teases an unexpected outcome to retain viewers.",
                tags=["shock", "unexpected", "cliffhanger"],
            ),
            # Pattern interruption and immediate value
            HookTemplate(
                text="Stop scrolling! Here's the one thing you need to know ...",
                description="Pattern interrupt with an immediate value proposition.",
                tags=["pattern_break", "value", "curiosity"],
            ),
            # Relatable regret and learning
            HookTemplate(
                text="I wish I knew this earlier ...",
                description="Relatable regret leading to a valuable tip.",
                tags=["relatable", "curiosity", "tip"],
            ),
            # Urgency and FOMO
            HookTemplate(
                text="Do this before it's too late ...",
                description="Urgency and FOMO to drive immediate action.",
                tags=["urgency", "fomo", "shock"],
            ),
            # Storytelling with actionable promise
            HookTemplate(
                text="This one skill changed my life — and it takes 2 minutes a day",
                description="Storytelling with an actionable promise.",
                tags=["story", "promise", "curiosity"],
            ),
            # List format highlighting problems and solutions
            HookTemplate(
                text="3 reasons why your videos aren't taking off (and how to fix them)",
                description="List format highlighting common mistakes and solutions.",
                tags=["list", "problem", "solution", "curiosity"],
            ),
            # Tribal language and shock
            HookTemplate(
                text="Most people are doing this WRONG ...",
                description="Tribal language that creates an in-group vs out-group dynamic.",
                tags=["tribal", "shock", "tease"],
            ),
            # Curiosity-driven evaluation
            HookTemplate(
                text="Is it worth it? Let's find out!",
                description="Curiosity-driven evaluation hooking viewers to see the conclusion.",
                tags=["curiosity", "evaluation", "anticipation"],
            ),
            # Transformation and speed
            HookTemplate(
                text="Watch me transform this in 10 seconds!",
                description="Transformation hook emphasising speed and impact.",
                tags=["transformation", "shock", "speed"],
            ),
            # Novel combination mash-up
            HookTemplate(
                text="Here's what happens when you combine X and Y ...",
                description="Mash-up hook inviting viewers to see a novel combination.",
                tags=["mix", "curiosity", "innovation"],
            ),
            # Hype and challenge
            HookTemplate(
                text="You're not ready for this ...",
                description="Hype and challenge to entice viewers to prove themselves.",
                tags=["challenge", "hype", "shock"],
            ),
        ]

    def generate_hooks(self, platform: str, count: int = 5) -> List[HookTemplate]:
        """Return a random selection of hooks for the specified platform.

        Args:
            platform: The target platform (e.g., 'tiktok', 'youtube').
            count: Number of hooks to return.

        Returns:
            A list of ``HookTemplate`` objects.
        """
        # In future versions, platform-specific filtering can be applied.
        return random.sample(self.library, k=min(count, len(self.library)))

    def evaluate_hook(self, hook: HookTemplate) -> float:
        """Estimate the effectiveness of a hook using weighted tag heuristics.

        Each tag contributes a predefined weight to the base score.  Tags
        associated with high-retention psychological principles (e.g.,
        curiosity gaps, anticipation, urgency) are weighted more
        heavily.  A small random factor is added to diversify
        selection.  The resulting score is capped at 1.0.

        Args:
            hook: A ``HookTemplate`` object.

        Returns:
            A float between 0 and 1 representing the relative
            effectiveness of the hook.
        """
        # Define per-tag weights reflecting psychological potency
        weights: Dict[str, float] = {
            'curiosity': 0.3,
            'anticipation': 0.25,
            'shock': 0.2,
            'pattern_break': 0.15,
            'value': 0.15,
            'relatable': 0.1,
            'tip': 0.1,
            'urgency': 0.2,
            'fomo': 0.15,
            'story': 0.2,
            'promise': 0.15,
            'list': 0.1,
            'problem': 0.1,
            'solution': 0.1,
            'tribal': 0.1,
            'tease': 0.15,
            'evaluation': 0.15,
            'transformation': 0.25,
            'speed': 0.1,
            'mix': 0.15,
            'innovation': 0.15,
            'challenge': 0.2,
            'hype': 0.15,
            'twist': 0.15,
            'dopamine': 0.2,
            'unexpected': 0.2,
            'cliffhanger': 0.2,
            'secret': 0.2,
        }
        # Sum the weights for all tags present; default to 0.05 for unknown tags
        base_score = 0.0
        for tag in hook.tags:
            base_score += weights.get(tag, 0.05)
        # Cap the base score at 1.0
        base_score = min(base_score, 1.0)
        # Add a small random factor (0–0.05) to diversify ranking
        base_score += random.random() * 0.05
        return min(base_score, 1.0)

    def rank_hooks(self, hooks: List[HookTemplate]) -> List[Tuple[HookTemplate, float]]:
        """Rank hooks based on their heuristic score.

        Args:
            hooks: A list of hook templates.

        Returns:
            A sorted list of tuples (hook, score) descending by score.
        """
        scored = [(hook, self.evaluate_hook(hook)) for hook in hooks]
        return sorted(scored, key=lambda h: h[1], reverse=True)
