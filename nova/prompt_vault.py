"""Prompt Vault Module.

This module implements a lightweight store for managing the lifecycle
of prompts used in the content engine.  It supports saving and
loading prompts to/from disk, recording performance metrics and
retiring underperforming prompts.  Each prompt is represented as a
dictionary with at minimum an ``id`` and ``text`` field.

Usage:
    vault = PromptVault('reports/prompt_vault.json')
    vault.load()
    vault.add_prompt({'id': '123', 'text': 'Example prompt', 'active': True})
    vault.save()
    retired = vault.retire_prompts(['123'])

The ``auto_retire`` method integrates with ``PromptLeaderboard`` to
remove a percentage of prompts based on performance.
"""

from __future__ import annotations

import json
from typing import List, Dict, Optional

from .rpm_leaderboard import PromptLeaderboard


class PromptVault:
    """Maintains a persistent store of prompts."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.prompts: Dict[str, Dict] = {}

    def load(self) -> None:
        """Load prompts from disk if the file exists."""
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.prompts = {p["id"]: p for p in data}
        except FileNotFoundError:
            self.prompts = {}

    def save(self) -> None:
        """Persist all prompts to disk."""
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(list(self.prompts.values()), f, indent=2)

    def add_prompt(self, prompt: Dict) -> None:
        """Add a new prompt to the vault.

        Args:
            prompt: A dictionary containing at least ``id`` and ``text`` keys.
        """
        self.prompts[prompt["id"]] = prompt

    def retire_prompts(self, ids: List[str]) -> List[str]:
        """Retire the specified prompts by marking them inactive.

        Args:
            ids: List of prompt identifiers to retire.

        Returns:
            List of retired IDs.
        """
        retired = []
        for pid in ids:
            if pid in self.prompts:
                self.prompts[pid]["active"] = False
                retired.append(pid)
        return retired

    def auto_retire(self, leaderboard: PromptLeaderboard, percent: float = 10.0) -> List[str]:
        """Retire the bottom percentage of prompts based on the leaderboard.

        Args:
            leaderboard: A ``PromptLeaderboard`` instance with current metrics.
            percent: Percentage of prompts to retire (0-100).

        Returns:
            List of retired prompt IDs.
        """
        retired_ids = leaderboard.retire_bottom_percent(percent)
        return self.retire_prompts(retired_ids)
