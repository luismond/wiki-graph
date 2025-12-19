"""Unit tests for the uap-ent project."""

from wiki_page import WikiPage as wp


def test_wiki_page():
    """Test the WikiPage class."""
    wiki_page = wp(page_name="London", lang_code='en')
    assert wiki_page.soup is not None
    assert wiki_page.get_soup() is not None
    assert wiki_page.download_soup() is not None
    assert wiki_page.paragraphs is not None
    assert len(wiki_page.paragraphs) > 0
    assert wiki_page.soup.title.string == "London"
    assert wiki_page.shortdescription is not None
    assert wiki_page.url is not None
    assert wiki_page.get_languages() is not None


def test_wiki_page_es():
    """Test the WikiPage class."""
    wiki_page = wp(page_name="Londres", lang_code='es')
    assert wiki_page.soup is not None
    assert wiki_page.get_soup() is not None
    assert wiki_page.download_soup() is not None
    assert wiki_page.paragraphs is not None
    assert len(wiki_page.paragraphs) > 0
    assert wiki_page.soup.title.string == "Londres"
    assert wiki_page.shortdescription is not None
    assert wiki_page.url is not None
    assert wiki_page.get_languages() is not None


def test_wiki_page_de():
    """Test the WikiPage class."""
    wiki_page = wp(page_name="London", lang_code='de')
    assert wiki_page.soup is not None
    assert wiki_page.get_soup() is not None
    assert wiki_page.download_soup() is not None
    assert wiki_page.paragraphs is not None
    assert len(wiki_page.paragraphs) > 0
    assert wiki_page.soup.title.string == "London"
    assert wiki_page.shortdescription is not None
    assert wiki_page.url is not None
    assert wiki_page.get_languages() is not None


def test_wiki_page_fr():
    """Test the WikiPage class."""
    wiki_page = wp(page_name="Londres", lang_code='fr')
    assert wiki_page.soup is not None
    assert wiki_page.get_soup() is not None
    assert wiki_page.download_soup() is not None
    assert wiki_page.paragraphs is not None
    assert len(wiki_page.paragraphs) > 0
    assert wiki_page.soup.title.string == "Londres"
    assert wiki_page.shortdescription is not None
    assert wiki_page.url is not None
    assert wiki_page.get_languages() is not None


def test_wiki_page_pt():
    """Test the WikiPage class."""
    wiki_page = wp(page_name="Londres", lang_code='pt')
    assert wiki_page.soup is not None
    assert wiki_page.get_soup() is not None
    assert wiki_page.download_soup() is not None
    assert wiki_page.paragraphs is not None
    assert len(wiki_page.paragraphs) > 0
    assert wiki_page.soup.title.string == "Londres"
    assert wiki_page.shortdescription is not None
    assert wiki_page.url is not None
    assert wiki_page.get_languages() is not None


def test_wiki_page_it():
    """Test the WikiPage class."""
    wiki_page = wp(page_name="Londra", lang_code='it')
    assert wiki_page.soup is not None
    assert wiki_page.get_soup() is not None
    assert wiki_page.download_soup() is not None
    assert wiki_page.paragraphs is not None
    assert len(wiki_page.paragraphs) > 0
    assert wiki_page.soup.title.string == "Londra"
    assert wiki_page.shortdescription is not None
    assert wiki_page.url is not None
    assert wiki_page.get_languages() is not None