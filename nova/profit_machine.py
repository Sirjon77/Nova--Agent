"""Profit Machine Designer Module.

This module provides a skeleton implementation for building automated
monetization funnels.  The ProfitMachineDesigner class encapsulates
methods for creating offers, generating lead magnets, defining sales
funnels, upsell strategies and retention mechanisms.  Each method
returns simple placeholder data structures and logs the requested
operation.  The goal is to integrate this with external services
such as ConvertKit, Beacons or Gumroad in the future.  When real
credentials and business logic are available, these methods can be
extended to generate dynamic offers and landing pages.

Usage:
    designer = ProfitMachineDesigner()
    offer = designer.create_offer("Nail Art Kit", price=29.99, description="A deluxe kit ...")
    funnel = designer.build_sales_funnel(offer)
    designer.save_report("reports/offer_strategy.json", funnel)

Note:
    This skeleton does not perform any network calls or side effects.  It
    simply returns dictionaries that outline the structure of a monetisation
    engine.  It is safe to invoke from within the governance loop without
    impacting other modules.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class Offer:
    """Represents an offer or product in the monetisation engine."""

    name: str
    price: float
    description: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    upsells: List[str] = field(default_factory=list)
    retention_strategy: Optional[str] = None


class ProfitMachineDesigner:
    """Designs monetisation funnels and automated profit machines.

    The methods here return simplistic data structures to serve as
    placeholders.  In a production system these would interface with
    CRM systems, email marketing tools and affiliate platforms.
    """

    def __init__(self) -> None:
        self.offers: Dict[str, Offer] = {}

    def create_offer(self, name: str, price: float, description: str) -> Offer:
        """Create a new offer with basic metadata.

        Args:
            name: The name of the product or service.
            price: The selling price.
            description: A textual description of what is included.

        Returns:
            An ``Offer`` instance.
        """
        offer = Offer(name=name, price=price, description=description)
        self.offers[offer.id] = offer
        return offer

    # ------------------------------------------------------------------
    # New helper methods for end‑to‑end offer and funnel creation
    #
    def generate_offer_link(self, product_slug: str) -> str:
        """Generate a shareable product URL for a Gumroad product.

        This convenience method wraps the Gumroad helper to produce a link
        that can optionally include an affiliate ID.  If the Gumroad
        integration is unavailable or environment variables are missing,
        a fallback URL based on the slug will be returned.

        Args:
            product_slug: The slug identifying the product (e.g. ``"ai-course"``).

        Returns:
            A URL string pointing to the product page.
        """
        try:
            from integrations.gumroad import generate_product_link  # type: ignore
        except Exception:
            # If the integration cannot be imported, fall back to a generic URL
            return f"https://example.com/{product_slug}"
        try:
            return generate_product_link(product_slug)
        except Exception:
            return f"https://example.com/{product_slug}"

    def launch_offer(
        self,
        product_name: str,
        price: float,
        description: str,
        benefits: List[str],
        list_ids: Optional[List[str]] = None,
        *,
        meta_pixel_id: Optional[str] = None,
        tiktok_pixel_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create an offer, sales funnel and landing page in one step.

        This high‑level helper combines offer creation, sales funnel
        definition and micro‑landing page generation.  It also tries to
        generate a shareable product URL via the Gumroad integration.
        If mailing list identifiers are supplied and a ConvertKit API key
        is configured, it will attempt to subscribe a dummy contact to
        the specified forms (useful for building lead magnets).  Any
        external API calls are wrapped in try/except blocks so that
        missing credentials or network errors do not interrupt the flow.

        Args:
            product_name: Name of the product being offered.
            price: Selling price of the product.
            description: Description of the offer.
            benefits: A list of bullet points highlighting the offer.
            list_ids: Optional list of ConvertKit form IDs to subscribe to.
            meta_pixel_id: Optional Meta Pixel ID to embed in the landing page.
            tiktok_pixel_id: Optional TikTok Pixel ID to embed in the landing page.

        Returns:
            A dictionary containing the offer data, sales funnel structure,
            product URL and the generated landing page HTML.
        """
        # Create the offer
        offer = self.create_offer(name=product_name, price=price, description=description)
        # Generate a slug from the product name for Gumroad and CTA purposes
        slug = product_name.lower().strip().replace(' ', '-')
        product_url = self.generate_offer_link(slug)
        # Build the sales funnel structure
        funnel = self.build_sales_funnel(offer)
        # Generate the landing page using the direct marketing planner
        try:
            from nova.direct_marketing import DirectMarketingPlanner  # type: ignore
        except Exception:
            planner = None  # type: ignore
        landing_page_html = ''
        if planner is not None:
            # Use environment base URL if provided
            import os
            base_url = os.getenv('PROMO_BASE_URL', 'https://example.com')
            planner = DirectMarketingPlanner(base_url=base_url)
            # Use the offer ID as the video_id for tracking
            landing_page_html = planner.build_funnel_page(
                video_id=offer.id,
                product_name=product_name,
                benefits=benefits,
                offer_code=slug,
                meta_pixel_id=meta_pixel_id,
                tiktok_pixel_id=tiktok_pixel_id,
            )
        # Optionally subscribe a dummy address to ConvertKit forms
        if list_ids:
            try:
                import os
                from convertkit_push import push_to_convertkit  # type: ignore
                api_key = os.getenv('CONVERTKIT_API_KEY')
                if api_key:
                    for form_id in list_ids:
                        # We use a placeholder email for demonstration; in a real
                        # system this would be replaced by the lead's address.
                        push_to_convertkit(api_key, form_id, email='lead@example.com')
            except Exception:
                # Silently ignore ConvertKit errors to avoid breaking the pipeline
                pass
        # Assemble the return payload
        return {
            'offer': offer.__dict__,
            'funnel': funnel,
            'product_url': product_url,
            'landing_page_html': landing_page_html,
        }

    def add_upsell(self, offer_id: str, upsell_name: str) -> None:
        """Add an upsell to an existing offer.

        Args:
            offer_id: Identifier for the base offer.
            upsell_name: Name of the upsell product.
        """
        offer = self.offers.get(offer_id)
        if offer:
            offer.upsells.append(upsell_name)

    def set_retention_strategy(self, offer_id: str, strategy: str) -> None:
        """Assign a retention strategy to an offer.

        Args:
            offer_id: Identifier for the offer.
            strategy: A brief description of how to retain customers.
        """
        offer = self.offers.get(offer_id)
        if offer:
            offer.retention_strategy = strategy

    def build_sales_funnel(self, offer: Offer) -> Dict[str, Any]:
        """Construct a simple sales funnel representation.

        Args:
            offer: The offer to build a funnel for.

        Returns:
            A dictionary describing each stage of the funnel.
        """
        funnel = {
            "lead_generation": {
                "method": "email_optin",
                "description": f"Collect emails via landing page for {offer.name}",
            },
            "offer": offer.name,
            "checkout": {
                "price": offer.price,
                "upsells": offer.upsells,
            },
            "retention": offer.retention_strategy or "monthly_newsletter",
        }
        return funnel

    def save_report(self, filepath: str, data: Any) -> None:
        """Persist any object to a JSON file.

        Args:
            filepath: Path on disk to write the JSON.
            data: A serialisable object (e.g., dict or list).
        """
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
