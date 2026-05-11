"""
Inverted index: term -> URL -> {frequency, positions}.
Search terms are normalised to lower case.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .crawler import Crawler

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?", re.IGNORECASE)  # Tokenise on alphanumeric sequences, allowing apostrophes within words (e.g., "don't")


def tokenize(text: str) -> list[str]:
    """Split visible page text into lower-case word tokens."""
    return [m.group(0).lower() for m in _TOKEN_RE.finditer(text)]


def _copy_posting(stats: dict[str, Any]) -> dict[str, Any]:
    return {"frequency": stats["frequency"], "positions": list(stats["positions"])}


class Indexer:
    """
    Nested-dict inverted index: ``index[term][url]`` holds posting statistics.

    Each posting is ``{"frequency": int, "positions": list[int]}`` where
    ``positions`` are 0-based indices of the token in that page's token stream.
    """

    def __init__(self) -> None:
        self._index: dict[str, dict[str, dict[str, Any]]] = {}

    def clear(self) -> None:
        self._index.clear()

    def add_document(self, url: str, text: str) -> None:
        """Merge one crawled page into the index (call for each crawl yield)."""
        for position, term in enumerate(tokenize(text)):  # For each token, add to the index
            by_url = self._index.setdefault(term, {})
            stats = by_url.setdefault(
                url,
                {"frequency": 0, "positions": []},
            )
            stats["frequency"] += 1
            stats["positions"].append(position)

    def crawl_and_index(self, crawler: Crawler, max_pages: int | None = None) -> int:
        """
        Run the crawler and index each page as it arrives.
        Returns the number of successfully indexed pages.
        """
        n = 0
        for url, text in crawler.crawl(max_pages=max_pages):
            self.add_document(url, text)
            n += 1
        return n

    def lookup(self, term: str) -> dict[str, dict[str, Any]]:
        """All URLs containing ``term`` (case-insensitive), with posting copies."""
        inner = self._index.get(term.lower())
        if not inner:
            return {}
        return {url: _copy_posting(stats) for url, stats in inner.items()}

    @property
    def inverted_index(self) -> dict[str, dict[str, dict[str, Any]]]:
        """Full index: shallow copy of URLs; postings are copied."""
        return {
            term: {url: _copy_posting(stats) for url, stats in by_url.items()}
            for term, by_url in self._index.items()
        }

    def save(self, path: str | Path) -> None:
        """Write the full inverted index to a single JSON file."""
        p = Path(path)
        p.write_text(json.dumps(self._index, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> Indexer:
        """Load an index previously written with save method."""
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(str(p))
        data: dict[str, dict[str, dict[str, Any]]] = json.loads(
            p.read_text(encoding="utf-8")
        )
        obj = cls()
        obj._index = data
        return obj
