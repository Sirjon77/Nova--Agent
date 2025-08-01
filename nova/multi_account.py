"""Multi-account distribution module.

This helper coordinates posting content across multiple accounts on the
same social platform.  It takes a mapping of platforms to account
identifiers and uses the ``PostAdapter`` to adapt captions and
call‑to‑actions (CTAs) for each account.  The resulting list of
objects indicates which account to post to along with the adapted
content.  In the future this module could be extended to enqueue
tasks into the task manager for each account or to interface with
platform‑specific SDKs.

Example:

    from nova.multi_account import MultiAccountDistributor
    distributor = MultiAccountDistributor({"tiktok": ["brand1", "brand2"]})
    posts = distributor.distribute(
        platform="tiktok",
        base_caption="Discover our new product",
        base_cta="Check the link in bio"
    )
    for post in posts:
        print(post["account"], post["caption"], post["cta"])

"""

from __future__ import annotations

from typing import Dict, List

from nova.multi_platform import PostAdapter


class MultiAccountDistributor:
    """Distribute content across multiple accounts on a platform.

    The distributor reads a mapping of platforms to account identifiers
    and uses the ``PostAdapter`` to tailor captions and CTAs per
    platform.  It returns a list of dictionaries where each entry
    contains the target account and the adapted content for that
    account.  If no accounts are configured for a platform, an
    empty list is returned.
    """

    def __init__(self, accounts: Dict[str, List[str]]) -> None:
        # Normalise platform keys to lowercase for case-insensitive lookup
        self.accounts: Dict[str, List[str]] = {k.lower(): v for k, v in accounts.items()}
        self.adapter = PostAdapter()

    def distribute(self, platform: str, base_caption: str, base_cta: str) -> List[Dict[str, str]]:
        """Generate content packages for each account on a platform.

        Args:
            platform: Name of the platform (e.g. 'tiktok', 'instagram').
            base_caption: The base caption to adapt per account.
            base_cta: The base call‑to‑action to adapt per account.

        Returns:
            A list of dictionaries with keys ``account``, ``caption`` and
            ``cta``.  Each entry corresponds to a configured account.
            If the platform has no associated accounts, an empty list
            is returned.
        """
        results: List[Dict[str, str]] = []
        platform_lc = platform.lower()
        acct_list = self.accounts.get(platform_lc, [])
        for acct in acct_list:
            caption = self.adapter.generate_caption(base_caption, platform_lc)
            cta = self.adapter.generate_cta(base_cta, platform_lc)
            results.append({
                'account': acct,
                'caption': caption,
                'cta': cta,
            })
        return results