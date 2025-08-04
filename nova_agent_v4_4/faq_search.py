"""Dummy FAQ search—replace with real implementation."""
from typing import Union

FAQS = {
    "pricing": "Our plans start at $19/month.",
    "support": "You can reach support at support@example.com.",
}

def faq_search(query: str) -> Union[str, None]:
    for key, answer in FAQS.items():
        if key in query.lower():
            return answer
    return None
