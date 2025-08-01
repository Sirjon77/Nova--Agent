"""Weekly Digest and Landing Page Automation.

This module automates the creation of a weekly performance digest
and the generation of micro‑landing pages for top prompts.  It
integrates the prompt metrics storage (``prompt_metrics.py``), the
direct marketing planner (``nova.direct_marketing.DirectMarketingPlanner``)
and Notion synchronisation (``notion_sync.py``).  When run,
``push_weekly_digest_to_notion`` gathers prompt statistics,
produces a textual summary and uploads it to a configured Notion
database.  Optionally, it can also generate HTML landing pages
for high‑performing prompts and save them to disk for use with
email or funnel builders.

Environment variables expected:

    NOTION_TOKEN:
        Personal integration token with edit rights to your Notion
        workspace.  Required to create pages via the Notion API.

    NOTION_DATABASE_ID:
        The ID of the database where new digest pages will be
        created.  Can be found in the URL of your Notion database.

Usage example::

    from marketing_digest import push_weekly_digest_to_notion

    # Generate digest and upload to Notion
    push_weekly_digest_to_notion()

    # Generate landing pages for top prompts and write to files
    from marketing_digest import generate_landing_pages_for_top_prompts
    generate_landing_pages_for_top_prompts(num_pages=3, output_dir="landing_pages")

These functions can be integrated into the governance or analytics
pipeline to provide regular reporting and monetisation collateral
automatically.
"""

from __future__ import annotations

import os
import datetime
from typing import List, Dict, Any

from prompt_metrics import _load_metrics
from nova.direct_marketing import DirectMarketingPlanner
from notion_sync import sync_to_notion


def _prepare_metrics_for_digest() -> List[Dict[str, Any]]:
    """Transform stored prompt metrics into digest‑friendly dicts.

    Returns:
        A list of dictionaries with keys 'title', 'rpm' and 'views'.
        The 'title' is derived from the prompt identifier.
    """
    data = _load_metrics()
    metrics_list: List[Dict[str, Any]] = []
    for pid, metrics in data.items():
        metrics_list.append(
            {
                'title': pid,
                'rpm': float(metrics.get('avg_rpm', 0.0)),
                'views': int(metrics.get('avg_views', 0)),
            }
        )
    return metrics_list


def push_weekly_digest_to_notion() -> None:
    """Generate a weekly digest and upload it to Notion.

    This function gathers all prompt metrics, uses the direct
    marketing planner to compose a digest and then creates a new
    page in the configured Notion database.  If the required
    environment variables are not set, the digest is printed to
    stdout instead of being uploaded.
    """
    # Prepare metrics and compose digest
    metrics = _prepare_metrics_for_digest()
    planner = DirectMarketingPlanner()
    digest = planner.generate_weekly_digest(metrics)
    today = datetime.date.today().isoformat()
    page_title = f"Weekly Digest {today}"

    notion_token = os.getenv('NOTION_TOKEN')
    notion_db_id = os.getenv('NOTION_DATABASE_ID')
    if notion_token and notion_db_id:
        # Prepare Notion page properties: We use a simple page with a
        # title and a rich text property called "Digest".  Adjust the
        # property names to match your Notion database schema.
        properties = {
            'Name': {
                'title': [
                    {
                        'type': 'text',
                        'text': {'content': page_title},
                    }
                ]
            },
            'Digest': {
                'rich_text': [
                    {
                        'type': 'text',
                        'text': {'content': digest},
                    }
                ]
            },
        }
        status, res = sync_to_notion(notion_db_id, properties, notion_token)
        if status >= 200 and status < 300:
            print(f"[marketing_digest] Uploaded weekly digest to Notion (status {status})")
        else:
            print(f"[marketing_digest] Failed to upload digest to Notion: {status} {res}")
    else:
        # If Notion credentials are missing, output digest to console
        print("[marketing_digest] NOTION_TOKEN or NOTION_DATABASE_ID not configured. Printing digest:")
        print(digest)


def generate_landing_pages_for_top_prompts(num_pages: int = 3, output_dir: str = 'landing_pages') -> List[str]:
    """Generate micro‑landing page HTML files for top prompts.

    This helper retrieves the highest‑RPM prompts from the metrics
    store, constructs a simple offer and CTA for each, and writes
    the resulting micro‑landing page HTML to the specified output
    directory.  The function returns a list of file paths to the
    generated pages.

    Args:
        num_pages: Number of top prompts to generate landing pages for.
        output_dir: Directory where HTML files will be saved.

    Returns:
        A list of file system paths to the generated HTML files.
    """
    data = _load_metrics()
    if not data:
        print("[marketing_digest] No metrics available; cannot generate landing pages.")
        return []
    # Sort prompts by average RPM in descending order
    sorted_prompts = sorted(data.items(), key=lambda kv: kv[1].get('avg_rpm', 0.0), reverse=True)
    top_prompts = sorted_prompts[:num_pages]
    planner = DirectMarketingPlanner(base_url=os.getenv('PROMO_BASE_URL', 'https://example.com'))
    os.makedirs(output_dir, exist_ok=True)
    generated_files: List[str] = []
    for pid, metrics in top_prompts:
        # Use the prompt ID as product name; in a real system you
        # might map prompts to actual products.
        product_name = pid
        benefits = [
            'Learn secrets to maximise RPM',
            'Discover proven hooks and formats',
            'Join a community of growth‑minded creators',
        ]
        cta = planner.build_cta(video_id=pid, offer_code='promo')
        html = planner.generate_micro_landing_page(
            product_name=product_name,
            benefits=benefits,
            cta=cta,
            image_url=None,
        )
        filename = os.path.join(output_dir, f"{pid.replace(' ', '_')}.html")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        generated_files.append(filename)
        print(f"[marketing_digest] Generated landing page: {filename}")
    return generated_files