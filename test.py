"""Unit tests for the wiki-ent project."""

from wiki_page import WikiPage as wp
from corpus_manager import CorpusManager
from crawler import Crawler
from db_util import get_db_info

def base_test(page_name, lang_code):
    """Base test, asserting that the WikiPage object is instantiated correctly."""
    wiki_page = wp(page_name=page_name, lang_code=lang_code)
    assert wiki_page.soup is not None
    assert wiki_page.get_soup() is not None
    assert wiki_page.download_soup() is not None
    assert wiki_page.paragraphs is not None
    assert len(wiki_page.paragraphs) > 0
    assert wiki_page.soup.title.string == page_name
    assert wiki_page.shortdescription is not None
    assert wiki_page.url is not None
    assert wiki_page.get_languages() is not None


# Tests for the supported languages.


def test_wiki_page_en(page_name="London", lang_code="en"):
    base_test(page_name, lang_code)


def test_wiki_page_es(page_name="Londres", lang_code="es"):
    base_test(page_name, lang_code)


def test_wiki_page_de(page_name="London", lang_code="de"):
    base_test(page_name, lang_code)


def test_wiki_page_fr(page_name="Londres", lang_code="fr"):
    base_test(page_name, lang_code)


def test_wiki_page_pt(page_name="Londres", lang_code="pt"):
    base_test(page_name, lang_code)


def test_wiki_page_it(page_name="Londra", lang_code="it"):
    base_test(page_name, lang_code)


def test_corpus_manager():
    cm = CorpusManager()
    assert cm.corpus is not None
    assert cm.corpus_embedding is not None
    assert cm.df is not None
    assert len(cm.corpus) > 0
    assert len(cm.corpus_embedding) > 0
    assert len(cm.df) > 0
    assert cm.corpus_embedding.shape[0] == cm.df.shape[0]
    df = cm.similarity_by_paragraphs(query='soccer')
    assert df is not None
    assert len(df) > 0


def test_db_info():
    info = get_db_info()
    assert info is not None
    assert len(info) > 0
    assert 'DB_NAME' in info
    assert 'pages' in info
    assert 'paragraph_corpus' in info
    assert 'page_links' in info
    assert 'page_autonyms' in info
    assert 'soups' in info


def test_crawler():
    seed_page_name = 'Association_football'
    cr = Crawler(seed_page_name=seed_page_name)
    assert cr.seed_page_name is not None
    assert cr.seed_paragraphs is not None
    assert len(cr.seed_paragraphs) > 0
    assert cr.seed_embedding is not None
    