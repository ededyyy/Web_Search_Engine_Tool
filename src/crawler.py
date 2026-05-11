"""
HTTP crawler for quotes.toscrape.com with a politeness delay for 6 seconds between requests.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_SEED = "https://quotes.toscrape.com/"
POLITENESS_SECONDS = 6.0

# User-Agent header for the crawler
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; CourseSearchBot/1.0; "
        "+https://example.edu/coursework)"
    ),
}


def normalize_url(base: str, href: str) -> str | None:
    """Join and defragment href; return None if not a crawlable http(s) URL."""
    if not href or href.startswith(("#", "javascript:", "mailto:")):  # Ignore anchors, javascript, and mailto links
        return None
    absolute = urljoin(base, href)
    clean, _frag = urldefrag(absolute)  # Defragment the URL to remove the fragment
    parsed = urlparse(clean)
    if parsed.scheme not in ("http", "https"):  # Only allow HTTP and HTTPS URLs
        return None
    return clean

# Check if the URL is on the same site
def same_site(url: str, allowed_netloc: str) -> bool:
    return urlparse(url).netloc.lower() == allowed_netloc.lower()


def visible_text(html: str) -> str:
    """Strip tags and script/style; collapse whitespace for downstream tokenisation."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):  # Remove script, style, and noscript tags
        tag.decompose()
    return " ".join(soup.get_text(separator=" ", strip=True).split())  # Join the text with a space and strip whitespace


class Crawler:
    """
    Breadth-first crawl of one host, POLITENESS_SECONDS between
    successive HTTP responses before the next request starts.
    """

    def __init__(
        self,
        seed_url: str = DEFAULT_SEED,
        politeness_seconds: float = POLITENESS_SECONDS,
        session: requests.Session | None = None,
    ) -> None:
        self.seed_url = urldefrag(seed_url)[0]  # Defrag the URL to remove the fragment
        parsed = urlparse(self.seed_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:  # Only allow HTTP and HTTPS URLs
            raise ValueError(f"Invalid seed URL: {seed_url!r}")
        self._allowed_netloc = parsed.netloc.lower()
        self._politeness = politeness_seconds
        self._session = session or requests.Session()
        self._session.headers.update(DEFAULT_HEADERS)
        self._last_fetch_end: float | None = None

    # Wait for the politeness delay
    def _wait_politeness(self) -> None:
        if self._last_fetch_end is None:
            return
        elapsed = time.monotonic() - self._last_fetch_end
        wait = self._politeness - elapsed
        if wait > 0:
            time.sleep(wait)

    # Fetch the URL
    def _fetch(self, url: str) -> str:
        self._wait_politeness()
        try:
            response = self._session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        finally:
            self._last_fetch_end = time.monotonic()

    # Extract the links from the HTML
    def extract_links(self, page_url: str, html: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        out: list[str] = []
        for a in soup.find_all("a", href=True):
            norm = normalize_url(page_url, a["href"])
            if norm and same_site(norm, self._allowed_netloc):
                out.append(norm)
        return out

    def crawl(
        self,
        max_pages: int | None = None,
    ) -> Iterator[tuple[str, str]]:
        """
        Yield (url, plain_text) for each discovered HTML page on the same host.
        Case-insensitive at query time.
        Text here is left as fetched so the indexer can lower-case when tokenising.
        """
        queue: list[str] = [self.seed_url]
        seen: set[str] = set()
        count = 0

        # Breadth-first crawl
        while queue:
            url = queue.pop(0)
            if url in seen:
                continue
            seen.add(url)

            try:
                html = self._fetch(url)
            except requests.RequestException as exc:
                logger.warning("Skip %s: %s", url, exc)
                continue

            text = visible_text(html)
            yield url, text
            count += 1
            if max_pages is not None and count >= max_pages:
                break

            for link in self.extract_links(url, html):
                if link not in seen:
                    queue.append(link)
