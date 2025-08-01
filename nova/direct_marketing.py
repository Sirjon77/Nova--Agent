"""Direct Marketing Planner Module.

This module provides basic utilities for constructing direct marketing
campaigns to supplement content monetisation.  It includes helper
functions to generate landing page outlines, email sequences and
affiliate link bundles.  The implementation is intentionally light to
avoid dependencies on external services.  It can be integrated with
platforms like ConvertKit, Gumroad or Beacons when credentials are
available.

The ``DirectMarketingPlanner`` class supports building micro-funnels
for each video prompt, including call-to-action (CTA) phrases,
landing page copy and email follow-ups.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class CTA:
    """Represents a call-to-action element."""

    text: str
    url: str


@dataclass
class LandingPage:
    """Represents a landing page blueprint."""

    headline: str
    subheadline: str
    benefits: List[str]
    cta: CTA


class DirectMarketingPlanner:
    """Constructs micro-funnels for direct marketing campaigns."""

    def __init__(self, base_url: str = "https://example.com/") -> None:
        self.base_url = base_url.rstrip("/")

    def build_cta(self, video_id: str, offer_code: str) -> CTA:
        """Generate a simple CTA with a trackable URL.

        Args:
            video_id: Unique identifier for the content.
            offer_code: Identifier for the offer or affiliate product.

        Returns:
            A ``CTA`` instance.
        """
        url = f"{self.base_url}/promo/{offer_code}?ref={video_id}"
        text = "Tap to claim your exclusive offer!"
        return CTA(text=text, url=url)

    def create_landing_page(self, product_name: str, benefits: List[str], cta: CTA) -> LandingPage:
        """Construct a landing page outline for a product.

        Args:
            product_name: Name of the product or service.
            benefits: A list of bullet-point benefits.
            cta: Call-to-action object.

        Returns:
            A ``LandingPage`` instance.
        """
        headline = f"Discover {product_name}"
        subheadline = "Unlock the ultimate value with our exclusive offer."
        return LandingPage(headline=headline, subheadline=subheadline, benefits=benefits, cta=cta)

    def build_email_sequence(self, product_name: str, days: int = 3) -> List[str]:
        """Create a simple drip email sequence outline.

        Args:
            product_name: Name of the product being promoted.
            days: The number of follow-up emails.

        Returns:
            A list of email subject lines.
        """
        sequence = []
        for i in range(1, days + 1):
            sequence.append(
                f"Day {i}: {product_name} - Here's why you need it"
            )
        return sequence

    def generate_micro_landing_page(
        self,
        product_name: str,
        benefits: List[str],
        cta: CTA,
        image_url: str | None = None,
        *,
        meta_pixel_id: str | None = None,
        tiktok_pixel_id: str | None = None,
    ) -> str:
        """Generate a simple HTML micro‑landing page with optional tracking pixels.

        This helper produces a minimal HTML snippet designed for a
        micro‑landing page or Beacons/ConvertKit integration.  It
        includes a headline, optional hero image, subheadline,
        bullet‑point list of benefits and a styled CTA button.  The
        resulting HTML is self‑contained and can be embedded into
        external landing page builders or emails.  When pixel IDs
        are provided, the corresponding tracking scripts are injected
        into the page to enable retargeting via Meta (Facebook) or
        TikTok.

        Args:
            product_name: Name of the product being promoted.
            benefits: A list of benefits to highlight.
            cta: A CTA instance containing button text and URL.
            image_url: Optional URL to a hero image or product photo.
            meta_pixel_id: Optional Meta/Facebook pixel ID to embed.
            tiktok_pixel_id: Optional TikTok pixel ID to embed.

        Returns:
            A string containing the HTML for the micro‑landing page.
        """
        # Build landing page structure using existing helper to get subheadline
        page = self.create_landing_page(product_name, benefits, cta)
        html_parts: List[str] = [
            "<html>",
            "<head>",
            f"<title>{product_name}</title>",
            "<meta charset=\"utf-8\">",
            "</head>",
            "<body style=\"font-family:Arial, sans-serif; margin:0; padding:20px;\">",
            f"<h1 style=\"font-size:2em;margin-bottom:0.5em;\">{page.headline}</h1>",
        ]
        # Optional image
        if image_url:
            html_parts.append(
                f"<img src=\"{image_url}\" alt=\"{product_name}\" style=\"max-width:100%; height:auto; margin-bottom:1em;\">"
            )
        html_parts.append(
            f"<p style=\"font-size:1.1em;margin-bottom:1em;\">{page.subheadline}</p>"
        )
        # Benefits list
        if benefits:
            html_parts.append("<ul style=\"list-style:disc; padding-left:1.5em; margin-bottom:1em;\">")
            for benefit in benefits:
                html_parts.append(f"<li style=\"margin-bottom:0.5em;\">{benefit}</li>")
            html_parts.append("</ul>")
        # CTA button
        html_parts.append(
            f"<a href=\"{cta.url}\" style=\"display:inline-block;padding:12px 24px;background-color:#007bff;color:#ffffff;text-decoration:none;border-radius:4px;font-weight:bold;\">{cta.text}</a>"
        )
        # Inject Meta/Facebook pixel if provided.  We avoid f-strings for
        # large blocks of JavaScript containing braces by using a
        # placeholder that we replace manually.  This prevents Python from
        # misinterpreting the braces as formatting expressions.
        if meta_pixel_id:
            meta_template = (
                "<script>!function(f,b,e,v,n,t,s){{if(f.fbq)return;n=f.fbq=function(){{n.callMethod? n.callMethod.apply(n,arguments):n.queue.push(arguments)}}; "
                "if(!f._fbq)f._fbq=n; n.push=n; n.loaded=0;n.version='2.0'; n.queue=[]; t=b.createElement(e); t.async=1; t.src=v; s=b.getElementsByTagName(e)[0]; "
                "s.parentNode.insertBefore(t,s);}}(window, document,'script','https://connect.facebook.net/en_US/fbevents.js'); "
                "fbq('init', '__META_PIXEL_ID__'); fbq('track', 'PageView');</script>"
                "<noscript><img height='1' width='1' style='display:none' "
                "src='https://www.facebook.com/tr?id=__META_PIXEL_ID__&ev=PageView&noscript=1'/></noscript>"
            )
            html_parts.append(meta_template.replace('__META_PIXEL_ID__', meta_pixel_id))
        # Inject TikTok pixel if provided
        if tiktok_pixel_id:
            tiktok_template = (
                "<script>!function (w, d, t) {{ w.TiktokAnalyticsObject=t; var ttq=w[t]=w[t]||[]; "
                "ttq.methods=['page','track','identify','instances','debug','on','off','once','ready','alias','group','enableCookie','disableCookie']; "
                "ttq.setAndDefer=function(obj,method){{obj[method]=function(){{obj.push([method].concat(Array.prototype.slice.call(arguments,0)))}}}}; "
                "for(var i=0; i<ttq.methods.length; i++) ttq.setAndDefer(ttq,ttq.methods[i]); "
                "ttq.instance=function(id){{var inst=ttq._i[id]||[]; for(var j=0; j<ttq.methods.length; j++) ttq.setAndDefer(inst,ttq.methods[j]); return inst}}; "
                "ttq.load=function(id,opts){{var url='https://analytics.tiktok.com/i18n/pixel/events.js'; ttq._i=ttq._i||{}; ttq._i[id]=[]; ttq._i[id]._u=url; ttq._t=ttq._t||{}; ttq._t[id]=+new Date; ttq._o=ttq._o||{}; ttq._o[id]=opts||{}; "
                "var s=d.createElement('script'); s.type='text/javascript'; s.async=1; s.src=url+'?sdkid='+id+'&lib='+t; var n=d.getElementsByTagName('script')[0]; n.parentNode.insertBefore(s,n)}; "
                "ttq.load('__TIKTOK_PIXEL_ID__'); ttq.page(); }}(window, document, 'ttq');</script>"
            )
            html_parts.append(tiktok_template.replace('__TIKTOK_PIXEL_ID__', tiktok_pixel_id))
        html_parts.extend(["</body>", "</html>"])
        return "".join(html_parts)

    def build_funnel_page(
        self,
        video_id: str,
        product_name: str,
        benefits: List[str],
        offer_code: str,
        *,
        meta_pixel_id: str | None = None,
        tiktok_pixel_id: str | None = None,
        image_url: str | None = None,
    ) -> str:
        """Create a complete funnel landing page for a video and offer.

        This convenience wrapper constructs a call‑to‑action (CTA), then
        builds a micro landing page containing the provided benefits and
        optional tracking pixels.  It combines the capabilities of
        ``build_cta`` and ``generate_micro_landing_page`` so that other
        modules (e.g. profit machine) can generate funnels with a
        single call.

        Args:
            video_id: Unique identifier for the video or prompt.
            product_name: Name of the product being promoted.
            benefits: A list of benefits to highlight on the landing page.
            offer_code: Code or slug used to construct the CTA URL.
            meta_pixel_id: Optional Meta/Facebook pixel ID for retargeting.
            tiktok_pixel_id: Optional TikTok pixel ID for retargeting.
            image_url: Optional image URL to include on the landing page.

        Returns:
            A string containing the HTML for the funnel landing page.
        """
        # Generate a CTA using the internal base URL and identifiers
        cta = self.build_cta(video_id=video_id, offer_code=offer_code)
        # Build the micro landing page with optional pixels
        return self.generate_micro_landing_page(
            product_name=product_name,
            benefits=benefits,
            cta=cta,
            image_url=image_url,
            meta_pixel_id=meta_pixel_id,
            tiktok_pixel_id=tiktok_pixel_id,
        )

    def generate_weekly_digest(self, metrics: List[Dict[str, Any]]) -> str:
        """Create a textual weekly performance digest from metrics.

        Given a list of metric dictionaries (e.g., one per video or
        prompt) containing keys such as 'title', 'rpm', 'views' and
        optional others, this method computes summary statistics and
        highlights the top performers.  The digest can be emailed to
        stakeholders or stored in the governance report for quick
        review.

        Args:
            metrics: A list of dictionaries where each entry represents
                metrics for a particular piece of content.  Expected
                keys include 'title' (str), 'rpm' (float) and 'views'
                (int).  Missing keys default to 0 or empty values.

        Returns:
            A multi‑line string summarising the week's performance.
        """
        if not metrics:
            return "No performance data available for this period."
        total_entries = len(metrics)
        total_views = sum(int(m.get('views', 0)) for m in metrics)
        total_rpm = sum(float(m.get('rpm', 0)) for m in metrics)
        avg_rpm = total_rpm / total_entries if total_entries else 0.0
        digest_lines: List[str] = []
        digest_lines.append("Weekly Performance Summary")
        digest_lines.append("==========================")
        digest_lines.append(f"Entries analysed: {total_entries}")
        digest_lines.append(f"Total views: {total_views}")
        digest_lines.append(f"Average RPM: {avg_rpm:.2f}")
        # Identify top 3 performers by RPM
        top_entries = sorted(metrics, key=lambda m: float(m.get('rpm', 0)), reverse=True)[:3]
        digest_lines.append("")
        digest_lines.append("Top performers:")
        for entry in top_entries:
            title = entry.get('title', 'Untitled')
            rpm = float(entry.get('rpm', 0))
            views = int(entry.get('views', 0))
            digest_lines.append(f"- {title}: RPM {rpm:.2f}, Views {views}")
        digest_lines.append("")
        digest_lines.append("Areas to watch:")
        # Flag entries with RPM below average
        lagging = [e for e in metrics if float(e.get('rpm', 0)) < avg_rpm]
        if not lagging:
            digest_lines.append("All entries performed at or above average RPM.")
        else:
            for entry in lagging[:3]:
                title = entry.get('title', 'Untitled')
                rpm = float(entry.get('rpm', 0))
                digest_lines.append(f"- {title}: RPM {rpm:.2f}")
        return "\n".join(digest_lines)
