"""Unit tests for the uap-ent project."""

from soup_utils import get_html_url, get_headers, download_soup


def test_get_html_url():
    """Test the get_html_url function."""
    assert get_html_url("London") == "https://api.wikimedia.org/core/v1/wikipedia/en/page/London/html"


def test_get_headers():
    """Test the get_headers function."""
    assert get_headers() is not None

def test_download_soup():
    """Test the download_soup function."""
    soup = download_soup("London")
    assert soup is not None
    assert soup.title.string == "London"


