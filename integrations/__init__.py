"""Integration helpers package for Nova Agent.

This package exposes helper functions for a variety of external services
that Nova interacts with.  Each integration is self-contained and
imported lazily to minimize overhead.  To use an integration, import
the desired helper function directly.  For example::

    from integrations import generate_affiliate_link, generate_product_link
    url = generate_affiliate_link("https://www.amazon.com/dp/B08CFSZLQ4")
    gumroad_link = generate_product_link("my-great-course")

The following helpers are provided:

* Amazon Associates: ``generate_affiliate_link``
* Gumroad: ``generate_product_link``, ``create_product``
* ConvertKit: ``subscribe_user``, ``add_tags_to_subscriber``
* Beacons: ``generate_profile_link``, ``update_links``
* HubSpot CRM: ``create_contact``
* Metricool: ``get_metrics``, ``get_overview``

See the individual modules for documentation and usage details.
"""

from .amazon_affiliate import generate_affiliate_link  # noqa: F401
from .gumroad import generate_product_link, create_product  # noqa: F401
from .convertkit import subscribe_user, add_tags_to_subscriber  # noqa: F401
from .beacons import generate_profile_link, update_links  # noqa: F401
from .hubspot import create_contact  # noqa: F401
from .metricool import get_metrics, get_overview  # noqa: F401
from .tubebuddy import search_keywords, get_trending_videos  # noqa: F401
from .socialpilot import schedule_post  # noqa: F401
from .publer import schedule_post as publer_schedule_post  # noqa: F401
from .translate import translate_text  # noqa: F401
from .vidiq import get_trending_keywords  # noqa: F401

# Video and audio publishing helpers
#
# These helpers allow Nova to upload videos directly to YouTube,
# publish video content to Instagram via the Graph API, publish posts
# (with optional media) to a Facebook Page, and synthesise speech
# from text using a third‑party TTS service. See the individual
# modules for details on required environment variables and usage.
from .youtube import upload_video  # noqa: F401
from .instagram import publish_video  # noqa: F401
from .facebook import publish_post  # noqa: F401
from .tts import synthesize_speech  # noqa: F401

__all__ = [
    "generate_affiliate_link",
    "generate_product_link",
    "create_product",
    "subscribe_user",
    "add_tags_to_subscriber",
    "generate_profile_link",
    "update_links",
    "create_contact",
    "get_metrics",
    "get_overview",
    "search_keywords",
    "get_trending_videos",
    "schedule_post",
    "publer_schedule_post",
    "translate_text",
    "get_trending_keywords",

    # Video and audio publishing
    "upload_video",
    "publish_video",
    "publish_post",
    "synthesize_speech",
]