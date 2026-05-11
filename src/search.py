"""
Query helpers: AND over query tokens, formatting postings.
"""

from __future__ import annotations
from typing import Any
from .indexer import Indexer, tokenize


def urls_matching_phrase(indexer: Indexer, phrase: str) -> list[str]:
    """
    URLs that contain every token in phrase (intersection).
    """
    terms = tokenize(phrase)  # Tokenise the query phrase
    if not terms:
        return []
    url_sets = [set(indexer.lookup(t).keys()) for t in terms]  # Get sets of URLs for each term
    return sorted(set.intersection(*url_sets))  # Return URLs that are in all sets (AND)


def format_term_postings(term: str, postings: dict[str, dict[str, Any]]) -> str:
    """Print inverted-index postings for one term."""
    # No entries for the term
    if not postings:
        return f"(no entries for {term!r})"
    lines = [f"Inverted index for {term!r}:"]  # Header line
    for url in sorted(postings):
        stats = postings[url]
        lines.append(f"  {url}")
        lines.append(f"    frequency: {stats['frequency']}")
        lines.append(f"    positions: {stats['positions']}")
    return "\n".join(lines)
