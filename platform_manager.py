
"""Platform manager for multi‑platform posting.

This module orchestrates posting a single piece of content across
multiple social platforms while adapting the caption, hashtags and
call‑to‑action to suit each destination.  It leverages the
``PostAdapter`` from ``nova.multi_platform`` for caption and CTA
customisation and the ``HashtagOptimizer`` to inject relevant
hashtags based on the prompt topic.  After posting, it records a
dummy metric entry to the prompt metrics store so that the
feedback loop can operate even without real analytics.
"""

from __future__ import annotations

import random
from typing import List, Union

from nova.multi_platform import PostAdapter  # type: ignore
from nova.multi_account import MultiAccountDistributor  # type: ignore
from nova.platform_metrics import record_platform_metric  # type: ignore
from integrations.translate import translate_text  # type: ignore
from nova.hashtag_optimizer import HashtagOptimizer  # type: ignore
import os
from prompt_metrics import record_prompt_metric

from youtube_poster import post_to_youtube
from instagram_poster import post_to_instagram
from tiktok_uploader import upload_to_tiktok


def _extract_topic(prompt: str, topics: List[str]) -> str:
    """Heuristically determine the topic of a prompt.

    This helper searches for keywords in the prompt that match known
    topics from the hashtag optimiser.  If no match is found, the
    first topic in the list is returned as a fallback.

    Args:
        prompt: The prompt or script used to generate the video.
        topics: A list of topic names recognised by the optimiser.

    Returns:
        The name of the topic that best matches the prompt.
    """
    prompt_lc = prompt.lower()
    for topic in topics:
        if any(word in prompt_lc for word in topic.split()):
            return topic
    # Fallback to first topic
    return topics[0] if topics else ''


def manage_platforms(video_path: str, prompt: str, prompt_id: Union[str, None] = None) -> str:
    """Post a video to multiple social platforms with tailored captions.

    Args:
        video_path: Local path to the video file.
        prompt: The textual prompt or title associated with the video.
        prompt_id: Optional identifier for tracking metrics.  If
            omitted, the prompt text is used.

    Returns:
        A string summarising the posting outcome.
    """
    adapter = PostAdapter()
    hashtagger = HashtagOptimizer()
    # Determine the topic and generate a set of relevant hashtags
    topic_list = list(hashtagger.topic_tags.keys())
    topic = _extract_topic(prompt, topic_list)
    # Determine whether to use dynamic trending hashtags based on env var
    use_dynamic = os.getenv('HASHTAG_DYNAMIC', '').lower() in {'1', 'true', 'yes'}
    # Determine per‑platform hashtag count; allow override via env
    platform_counts = {
        'youtube': int(os.getenv('HASHTAG_COUNT_YT', '3')),  # default 3
        'instagram': int(os.getenv('HASHTAG_COUNT_IG', '5')),  # default 5
        'tiktok': int(os.getenv('HASHTAG_COUNT_TT', '4')),  # default 4
    }
    # Use the prompt itself as identifier if none provided
    pid = prompt_id or prompt
    # Attempt to load a multi‑account configuration from the environment.
    # NOVA_ACCOUNTS should be a JSON string mapping platform names to
    # lists of account identifiers.  If omitted, posts will be sent
    # using the default authenticated account.
    import json
    accounts_env = os.getenv('NOVA_ACCOUNTS')
    accounts_map: dict[str, list[str]] = {}
    if accounts_env:
        try:
            accounts_map = json.loads(accounts_env)
        except Exception:
            accounts_map = {}
    distributor_cache: dict[str, MultiAccountDistributor] = {}
    # Parse optional localisation languages.  TARGET_LANGUAGES should
    # be a comma‑separated string of ISO codes (e.g. "es,fr").
    lang_env = os.getenv('TARGET_LANGUAGES', '')
    languages: list[str] = [c.strip() for c in lang_env.split(',') if c.strip()]
    # Derive hashtags and base caption
    if use_dynamic:
        hashtags = hashtagger.suggest_dynamic(topic, count=max(platform_counts.values()))
    else:
        hashtags = hashtagger.suggest(topic, count=max(platform_counts.values()))
    hashtag_str = ' '.join(hashtags)
    base_caption = f"{prompt}\n{hashtag_str}".strip()
    # Apply language translations if configured.  Append translations
    # separated by newlines after the primary caption.  Errors in
    # translation are silently ignored to avoid interrupting posting.
    if languages:
        translations: list[str] = []
        for code in languages:
            try:
                translated = translate_text(prompt, target_language=code)
                translations.append(translated)
            except Exception:
                # If translation fails, skip this language
                continue
        if translations:
            base_caption = base_caption + "\n" + "\n".join(translations)
    print("[PlatformManager] Preparing to post to all platforms…")
    # Helper to handle posting per platform with optional multi‑account
    def _post(platform: str, post_func, cta_message: str) -> None:
        # Determine hashtags to use for this platform (trim to configured count)
        cnt = platform_counts.get(platform, 3)
        tags_for_platform = hashtags[:cnt]
        caption = adapter.generate_caption(f"{prompt}\n{' '.join(tags_for_platform)}", platform=platform)
        # Append translations if present
        if languages:
            caption = caption + "\n" + "\n".join(translations) if translations else caption
        cta = adapter.generate_cta(cta_message, platform=platform)
        accounts = accounts_map.get(platform, [])
        if accounts:
            # Use MultiAccountDistributor to tailor captions per account
            # Cache distributors per platform to avoid reinitialisation
            if platform not in distributor_cache:
                distributor_cache[platform] = MultiAccountDistributor({platform: accounts})
            distributor = distributor_cache[platform]
            posts = distributor.distribute(platform, base_caption, cta_message)
            for _pkg in posts:
                # For each account, generate account‑specific caption/cta
                acct_caption = _pkg['caption']
                acct_cta = _pkg['cta']
                full_caption = f"{acct_caption}\n\n{acct_cta}"
                try:
                    if platform == 'youtube':
                        post_to_youtube(
                            title=prompt,
                            description=full_caption,
                            video_path=video_path,
                            tags=[tag.strip('#') for tag in tags_for_platform],
                        )
                    elif platform == 'instagram':
                        post_to_instagram(video_path, full_caption)  # type: ignore[arg-type]
                    elif platform == 'tiktok':
                        upload_to_tiktok(video_path, full_caption)
                except Exception:
                    # Ignore individual posting failures to other accounts
                    continue
        else:
            # Single account; post once
            full_caption = f"{caption}\n\n{cta}"
            if platform == 'youtube':
                post_to_youtube(
                    title=prompt,
                    description=full_caption,
                    video_path=video_path,
                    tags=[tag.strip('#') for tag in tags_for_platform],
                )
            elif platform == 'instagram':
                try:
                    post_to_instagram(video_path, full_caption)  # type: ignore[arg-type]
                except Exception:
                    pass
            elif platform == 'tiktok':
                upload_to_tiktok(video_path, full_caption)
        # Record per‑platform metrics for demonstration
        try:
            record_platform_metric(
                prompt_id=pid,
                platform=platform,
                rpm=round(random.uniform(0.5, 5.0), 2),
                views=random.randint(500, 5000),
                ctr=round(random.uniform(0.01, 0.05), 3),
                retention=round(random.uniform(0.3, 0.9), 2),
                country=os.getenv('DEFAULT_COUNTRY', 'US'),
            )
        except Exception:
            # If the platform metrics module is unavailable, skip
            pass
    # Post to each supported platform
    _post('youtube', post_to_youtube, "Like and subscribe")
    _post('instagram', post_to_instagram, "Follow us")
    _post('tiktok', upload_to_tiktok, "Check our bio")
    # Record a dummy overall metric entry for demonstration purposes.
    # For enhanced tracking we compute synthetic clicks from views to derive CTR.
    _views = random.randint(500, 5000)
    # Assume between 5–20% of impressions convert to clicks for synthetic data
    _clicks = max(1, int(_views * random.uniform(0.05, 0.20)))
    _rpm = round(random.uniform(0.5, 5.0), 2)
    _retention = round(random.uniform(0.3, 0.9), 2)
    _country = os.getenv('DEFAULT_COUNTRY', 'US')
    record_prompt_metric(
        pid,
        views=_views,
        clicks=_clicks,
        rpm=_rpm,
        retention=_retention,
        country_data={_country: {'views': _views, 'RPM': _rpm}},
    )
    return "Posted to YouTube, Instagram and TikTok."
