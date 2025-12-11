"""Unit tests for the uap-ent project."""

from wiki_page import WikiPage as wp


def test_wiki_page():
    """Test the WikiPage class."""
    wiki_page = wp("London")
    assert wiki_page.soup is not None
    assert wiki_page.paragraphs is not None
    assert wiki_page.soup.title.string == "London"

