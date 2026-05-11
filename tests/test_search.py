from src.indexer import Indexer
from src.search import format_term_postings, urls_matching_phrase


# Search tests
def test_urls_matching_phrase_single_term():
    indexer = Indexer()
    indexer.add_document("https://a/", "hello world")
    indexer.add_document("https://b/", "hello")

    assert urls_matching_phrase(indexer, "world") == ["https://a/"]  # Should return the URL that contains "world"

# Test that URLs matching all query terms are returned
def test_urls_matching_phrase_and_multiple_terms():
    indexer = Indexer()
    indexer.add_document("https://a/", "good friends here")
    indexer.add_document("https://b/", "good alone")
    indexer.add_document("https://c/", "friends only")

    assert urls_matching_phrase(indexer, "good friends") == ["https://a/"]  # Should return the URL that contains both "good" and "friends"

# Test the case-insensitive search
def test_urls_matching_phrase_case_insensitive():
    indexer = Indexer()
    indexer.add_document("https://a/", "Good FRIENDS")

    assert urls_matching_phrase(indexer, "good friends") == ["https://a/"]

# Empty query test
def test_urls_matching_phrase_empty_query():
    indexer = Indexer()
    indexer.add_document("https://a/", "word")

    assert urls_matching_phrase(indexer, "   ") == []

# Test that non-existent term returns empty list
def test_format_term_postings_empty():
    out = format_term_postings("nonsense", {})
    assert "no entries" in out.lower()
    assert "nonsense" in out

# Test that the output contains the URL, frequency, and positions for a term with postings
def test_format_term_postings_non_empty():
    postings = {
        "https://u/": {"frequency": 2, "positions": [0, 5]},
    }
    out = format_term_postings("foo", postings)
    assert "https://u/" in out
    assert "frequency: 2" in out
    assert "[0, 5]" in out or "0, 5" in out
