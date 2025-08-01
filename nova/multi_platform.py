"""Multi-platform posting adapter.

This module offers helper functions to adapt a base caption and
call-to-action for different social platforms.  Since each platform
has distinct character limits, tone preferences and hashtag
requirements, the ``PostAdapter`` class applies simple
transformations to optimise captions and CTAs per platform.

Examples:
    adapter = PostAdapter()
    caption = adapter.generate_caption("Learn nail art hacks", platform="instagram")
    cta = adapter.generate_cta("Check the link in bio", platform="tiktok")

Future enhancements may incorporate dynamic CTA scheduling or A/B
testing to fine-tune performance by country or demographic.
"""

from __future__ import annotations

from typing import Dict


class PostAdapter:
    """Adapt captions and CTAs for multiple platforms."""

    def generate_caption(self, base_caption: str, platform: str) -> str:
        """Return a caption tailored to a specific platform.

        Args:
            base_caption: The core message for the post.
            platform: Target platform (e.g., 'tiktok', 'instagram').

        Returns:
            A formatted caption string.
        """
        platform = platform.lower()
        if platform in ['instagram', 'facebook']:
            # Instagram and Facebook allow longer captions; emphasise storytelling
            caption = f"{base_caption}. What do you think? Let us know in the comments!"
        elif platform == 'tiktok':
            # TikTok captions should be brief with emojis
            caption = f"{base_caption} 😱👀"[:100]
        elif platform == 'youtube':
            # YouTube Shorts captions support hashtags; encourage subscription
            caption = f"{base_caption} | Subscribe for more!"
        else:
            caption = base_caption
        return caption

    def generate_cta(self, base_cta: str, platform: str) -> str:
        """Return a call-to-action formatted for the platform.

        Args:
            base_cta: The base CTA message.
            platform: Target platform name.

        Returns:
            A CTA string.
        """
        platform = platform.lower()
        if platform == 'tiktok':
            return f"{base_cta}! 👉 #ForYou"
        if platform == 'instagram':
            return f"{base_cta}! 💖 DM us your thoughts"
        if platform == 'facebook':
            return f"{base_cta}! 👍 Like and share"
        if platform == 'youtube':
            return f"{base_cta}! 🔔 Hit the bell"
        return base_cta
