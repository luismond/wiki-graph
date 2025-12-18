"""Unit tests for the uap-ent project."""

from wiki_page import WikiPage as wp


def test_wiki_page():
    """Test the WikiPage class."""
    wiki_page = wp("London")
    assert wiki_page.soup is not None
    assert wiki_page.get_soup() is not None
    assert wiki_page.download_soup() is not None
    assert wiki_page.paragraphs is not None
    assert len(wiki_page.paragraphs) > 0
    assert wiki_page.soup.title.string == "London"
    assert wiki_page.shortdescription is not None
    assert wiki_page.url is not None
    assert wiki_page.get_languages() is not None
