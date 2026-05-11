import pytest
from unittest.mock import Mock

from src.indexer import Indexer, tokenize


# Tokenisation tests
def test_tokenize_lowercases_words():
    # Mixed case should become separate lower-case tokens
    assert tokenize("Good LIFE") == ["good", "life"]


def test_tokenize_splits_on_punctuation():
    # Punctuation acts as a boundary between tokens
    assert tokenize("hello, world!") == ["hello", "world"]


def test_tokenize_empty_string():
    # Empty input should yield an empty list
    assert tokenize("") == []


def test_tokenize_apostrophe_inside_word():
    # Apostrophe may appear inside a token
    assert "don't" in tokenize("I don't know")


# Indexing: frequency and positions
def test_add_document_records_frequency_and_positions():
    indexer = Indexer()
    url = "https://example.com/a"

    indexer.add_document(url, "cat dog cat")

    cat = indexer.lookup("cat")
    assert cat[url]["frequency"] == 2
    assert cat[url]["positions"] == [0, 2]

    dog = indexer.lookup("dog")
    assert dog[url]["frequency"] == 1
    assert dog[url]["positions"] == [1]

# Multiple URLs for the same term
def test_add_document_same_term_two_urls():
    indexer = Indexer()

    indexer.add_document("https://a/", "alpha beta")
    indexer.add_document("https://b/", "beta alpha")

    alpha = indexer.lookup("alpha")
    assert alpha["https://a/"]["positions"] == [0]
    assert alpha["https://b/"]["positions"] == [1]


# Case-insensitive lookup
def test_lookup_is_case_insensitive():
    indexer = Indexer()
    indexer.add_document("https://x/", "Good GOOD good")

    assert indexer.lookup("good")["https://x/"]["frequency"] == 3
    assert indexer.lookup("GOOD")["https://x/"]["frequency"] == 3

# Lookup of unknown term returns empty dict
def test_lookup_unknown_term_returns_empty_dict():
    indexer = Indexer()
    indexer.add_document("https://x/", "only one word")

    assert indexer.lookup("missing") == {}


# inverted_index property and defensive copies
def test_inverted_index_matches_lookup_aggregation():
    indexer = Indexer()
    indexer.add_document("https://u/", "one two one")

    full = indexer.inverted_index
    assert "one" in full and "two" in full
    assert full["one"]["https://u/"]["frequency"] == 2
    assert full["two"]["https://u/"]["frequency"] == 1


def test_lookup_returns_copy_of_positions():
    # Mutating the returned list must not change internal index state
    indexer = Indexer()
    indexer.add_document("https://u/", "loop loop")

    posting = indexer.lookup("loop")["https://u/"]
    posting["positions"].append(99)

    again = indexer.lookup("loop")["https://u/"]
    assert again["positions"] == [0, 1]

# Clear method
def test_clear_removes_all_terms():
    indexer = Indexer()
    indexer.add_document("https://u/", "word")
    indexer.clear()

    assert indexer.lookup("word") == {}
    assert indexer.inverted_index == {}


# Integration with crawler (mocked): crawl and index
def test_crawl_and_index_counts_pages_and_indexes():
    indexer = Indexer()
    crawler = Mock()
    crawler.crawl.return_value = [
        ("https://quotes.toscrape.com/", "Hello world"),
        ("https://quotes.toscrape.com/page/2/", "world peace"),
    ]

    n = indexer.crawl_and_index(crawler, max_pages=None)

    assert n == 2
    crawler.crawl.assert_called_once_with(max_pages=None)

    hello = indexer.lookup("hello")
    assert "https://quotes.toscrape.com/" in hello
    assert hello["https://quotes.toscrape.com/"]["positions"] == [0]

    world_urls = indexer.lookup("world")
    assert set(world_urls) == {
        "https://quotes.toscrape.com/",
        "https://quotes.toscrape.com/page/2/",
    }


def test_crawl_and_index_passes_max_pages_to_crawl():
    indexer = Indexer()
    crawler = Mock()
    crawler.crawl.return_value = []

    indexer.crawl_and_index(crawler, max_pages=5)

    crawler.crawl.assert_called_once_with(max_pages=5)


# Save and load roundtrip
def test_save_load_roundtrip(tmp_path):
    indexer = Indexer()
    indexer.add_document("https://x/", "a b a")
    path = tmp_path / "idx.json"
    indexer.save(path)
    loaded = Indexer.load(path)
    assert loaded.lookup("a") == indexer.lookup("a")
    assert loaded.lookup("b") == indexer.lookup("b")

# Load missing file raises FileNotFoundError
def test_load_missing_file_raises(tmp_path):
    missing = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError):
        Indexer.load(missing)
