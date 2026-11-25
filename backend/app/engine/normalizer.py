"""Email text normalizer for OfferCheck.

Strips HTML, unescapes entities, normalizes Unicode (NFKC), and cleans whitespace.
"""
import html
import re
import unicodedata
from html.parser import HTMLParser
from typing import Optional


class _HTMLTagStripper(HTMLParser):
    """Robust HTML stripper that inserts linebreaks for block tags and spaces for inline tags."""

    def __init__(self) -> None:
        super().__init__()
        self.reset()
        self.fed: list[str] = []
        self._block_tags = {"p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr"}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag.lower() in self._block_tags:
            self.fed.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._block_tags:
            self.fed.append("\n")

    def handle_data(self, d: str) -> None:
        self.fed.append(d)

    def get_data(self) -> str:
        return "".join(self.fed)


def strip_html_tags(text: str) -> str:
    """Strip HTML tags while preserving structure and spacing."""
    if not text:
        return ""
    # Quick check if text contains HTML-like tags
    if "<" in text and ">" in text:
        try:
            stripper = _HTMLTagStripper()
            stripper.feed(text)
            text = stripper.get_data()
        except Exception:
            # Fallback to regex if malformed HTML causes parser issue
            text = re.sub(r"<[^>]+>", " ", text)
    return text


def normalize_email_text(raw_text: str) -> str:
    """Pipeline Step 1: Normalize email text for inspection.

    1. Strip HTML tags and replace block elements with spacing.
    2. Unescape all HTML entities (&amp;, &nbsp;, numeric entities).
    3. Normalize Unicode characters to NFKC (decomposes compatibility forms).
    4. Clean up carriage returns and collapse redundant whitespace while keeping paragraphs.
    """
    if not raw_text:
        return ""

    # 1. Strip HTML
    cleaned = strip_html_tags(raw_text)

    # 2. Unescape HTML entities
    cleaned = html.unescape(cleaned)

    # 3. Unicode NFKC normalization
    cleaned = unicodedata.normalize("NFKC", cleaned)

    # 4. Normalize line breaks and tabs
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    # Replace non-breaking spaces and zero-width spaces
    cleaned = cleaned.replace("\u00a0", " ").replace("\u200b", "")

    # Collapse multiple blank lines into max 2
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    # Collapse multiple horizontal spaces
    cleaned = re.sub(r"[ \t]+", " ", cleaned)

    return cleaned.strip()


# Alias for concise import
normalize_text = normalize_email_text


