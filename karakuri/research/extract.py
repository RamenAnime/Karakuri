"""Readable text and link extraction from fetched HTML.

The fetch layer stores raw response bodies. This module turns a body into the
parts the research worker actually wants: a title, clean visible text with
script and style noise removed, and the outbound links. BeautifulSoup is an
optional dependency (the ``research`` extra); when it is missing the functions
degrade to a regex based fallback so the core never hard depends on it.
"""

from __future__ import annotations

import re
from html import unescape
from urllib.parse import urljoin

try:
    from bs4 import BeautifulSoup

    _HAVE_BS4 = True
except ImportError:  # pragma: no cover - exercised only without the extra
    _HAVE_BS4 = False

_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.DOTALL | re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"[ \t\r\f\v]+")
_BLANKLINES_RE = re.compile(r"\n{3,}")
_HREF_RE = re.compile(r'href\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.DOTALL | re.IGNORECASE)


def extract_title(html: str) -> str | None:
    """Return the document title, or ``None`` when absent."""
    if _HAVE_BS4:
        soup = BeautifulSoup(html, "html.parser")
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        return None
    match = _TITLE_RE.search(html)
    if match:
        return unescape(match.group(1)).strip()
    return None


def extract_text(html: str) -> str:
    """Return readable visible text with scripts, styles, and tags removed."""
    if _HAVE_BS4:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text("\n")
    else:
        stripped = _SCRIPT_STYLE_RE.sub(" ", html)
        text = unescape(_TAG_RE.sub(" ", stripped))
    lines = [_WHITESPACE_RE.sub(" ", line).strip() for line in text.splitlines()]
    collapsed = "\n".join(line for line in lines if line)
    return _BLANKLINES_RE.sub("\n\n", collapsed).strip()


def extract_links(html: str, base_url: str | None = None) -> list[str]:
    """Return outbound links, resolved against ``base_url`` when given.

    Anchors, in-page fragments, and non http schemes are dropped. Order is
    preserved and duplicates are removed.
    """
    if _HAVE_BS4:
        soup = BeautifulSoup(html, "html.parser")
        raw = [a.get("href") for a in soup.find_all("a") if a.get("href")]
    else:
        raw = _HREF_RE.findall(html)

    seen: list[str] = []
    for href in raw:
        href = href.strip()
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue
        resolved = urljoin(base_url, href) if base_url else href
        if not resolved.startswith(("http://", "https://")):
            continue
        if resolved not in seen:
            seen.append(resolved)
    return seen
