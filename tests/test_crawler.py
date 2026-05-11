import pytest
import requests
from unittest.mock import Mock, patch

from src.crawler import (
    normalize_url,
    same_site,
    visible_text,
    Crawler,
)

# URL normalization tests
def test_normalize_relative_url():
    # Relative URL should be joined with base
    result = normalize_url(
        "https://quotes.toscrape.com",
        "/page/1/"
    )

    assert result == "https://quotes.toscrape.com/page/1/"

def test_normalize_removes_fragment():
    # Fragment should be removed from the URL
    result = normalize_url(
        "https://quotes.toscrape.com",
        "/page/1/#section"
    )

    assert result == "https://quotes.toscrape.com/page/1/"

def test_normalize_rejects_mailto():
    # Mailto links should be rejected
    result = normalize_url(
        "https://quotes.toscrape.com",
        "mailto:test@example.com"
    )

    assert result is None

def test_normalize_rejects_javascript():
    # Javascript links should be rejected
    result = normalize_url(
        "https://quotes.toscrape.com",
        "javascript:void(0)"
    )

    assert result is None

# Same site tests
def test_same_site_true():
    # URL with the same netloc should return True
    assert same_site(
        "https://quotes.toscrape.com/page/1/",
        "quotes.toscrape.com"
    )


def test_same_site_false():
    # URL with a different netloc should return False
    assert not same_site(
        "https://google.com",
        "quotes.toscrape.com"
    )

# Visible text tests
def test_visible_text_removes_script_and_style():
    html = """
    <html>
        <head>
            <style>body {color:red;}</style>
            <script>alert("hi")</script>
        </head>
        <body>
            <h1>Hello</h1>
            <p>World</p>
        </body>
    </html>
    """

    text = visible_text(html)

    assert "Hello" in text
    assert "World" in text
    assert "alert" not in text
    assert "color:red" not in text

# Extract links tests
def test_extract_links_same_site_only():
    # Only links on the same site should be extracted
    crawler = Crawler()

    html = """
    <html>
        <body>
            <a href="/page/1/">Page1</a>
            <a href="https://google.com">Google</a>
        </body>
    </html>
    """

    links = crawler._extract_links(
        "https://quotes.toscrape.com",
        html
    )

    assert "https://quotes.toscrape.com/page/1/" in links
    assert "https://google.com" not in links

# Fetch page tests
@patch("src.crawler.time.sleep")
def test_politeness_delay_called(mock_sleep):
    # Test if the politeness delay is called when _wait_politeness is invoked
    crawler = Crawler(politeness_seconds=6)

    crawler._last_fetch_end = 0

    with patch("src.crawler.time.monotonic", return_value=1):
        crawler._wait_politeness()

    mock_sleep.assert_called_once()


def test_fetch_returns_html():
    # Test if _fetch returns the HTML content of the page
    mock_session = Mock()

    mock_response = Mock()
    mock_response.text = "<html>Hello</html>"
    mock_response.raise_for_status.return_value = None

    mock_session.get.return_value = mock_response

    crawler = Crawler(session=mock_session)

    result = crawler._fetch("https://quotes.toscrape.com")

    assert result == "<html>Hello</html>"

# Crawl tests, checking if the process yields the expected pages and handles exceptions correctly
def test_crawl_yields_pages():
    crawler = Crawler()

    fake_html = """
    <html>
        <body>
            <p>Hello world</p>
        </body>
    </html>
    """

    with patch.object(crawler, "_fetch", return_value=fake_html):
        with patch.object(crawler, "_extract_links", return_value=[]):

            pages = list(crawler.crawl(max_pages=1))  # Only crawl one page for the test

    assert len(pages) == 1

    url, text = pages[0]

    # The URL should be the seed URL and the text should contain "Hello world"
    assert "quotes.toscrape.com" in url
    assert "Hello world" in text

# Test that crawl handles exceptions gracefully and continues crawling other pages
def test_crawl_handles_request_exception():
    crawler = Crawler()

    with patch.object(
        crawler,
        "_fetch",
        side_effect=requests.RequestException("Network error")
    ):

        pages = list(crawler.crawl(max_pages=1))

    assert pages == []


