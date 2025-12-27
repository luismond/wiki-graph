"""Unit tests for the wiki-ent project."""

from wiki_page import WikiPage as wp
from corpus_manager import CorpusManager, CorpusBitexts
from crawler import Crawler
from db_util import get_db_info
from __init__ import SEED_PAGE_NAME


def base_test(page_name, lang_code):
    """
    Base test, asserting that the WikiPage object is instantiated correctly.
    """
    wiki_page = wp(page_name=page_name, lang_code=lang_code)
    assert wiki_page.soup is not None
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


def test_db_info():
    """
    Test that get_db_info returns valid database info and expected tables.
    """
    info = get_db_info()
    assert info is not None
    assert len(info) > 0
    assert 'DB_NAME' in info
    assert 'pages' in info
    assert 'paragraph_corpus' in info
    assert 'page_links' in info
    assert 'page_autonyms' in info


def test_crawler():
    """
    Test that the Crawler object initializes properly,
    and all seed fields are present and valid.

    This test checks the following:
    - The seed_page_name attribute is set and not None.
    - The seed_paragraphs attribute is set, is not None,
      and has at least one element.
    - The seed_embedding attribute is set and not None.
    """
    cr = Crawler()
    assert cr.seed_page_name is not None
    assert cr.seed_paragraphs is not None
    assert len(cr.seed_paragraphs) > 0
    assert cr.seed_embedding is not None


def test_corpus_manager():
    """
    Test that the CorpusManager object loads the corpus, embeddings,
    and DataFrame properly.

    This test checks:
    - The corpus, corpus_embedding, and df attributes are populated
      and have correct lengths.
    - The shape of the embeddings matches the number of rows in the DataFrame.
    - The similarity_by_paragraphs method returns a valid DataFrame
      with similar paragraphs.
    """
    cm = CorpusManager()
    cm.load()
    assert cm.corpus is not None
    assert cm.corpus_embedding is not None
    assert cm.df is not None
    assert len(cm.corpus) > 0
    assert len(cm.corpus_embedding) > 0
    assert len(cm.df) > 0
    assert cm.corpus_embedding.shape[0] == cm.df.shape[0]
    df = cm.similarity_by_paragraphs(query=SEED_PAGE_NAME)
    assert df is not None
    assert len(df) > 0


def test_corpus_bitexts():
    """
    Test that the CorpusBitexts object loads parallel corpora and counts
     words correctly.

    This test checks:
    - The bitext DataFrame is loaded, is not None, and has at least one row.
    - The total word count is computed and is not None.
    """
    cb = CorpusBitexts()
    assert cb.df is not None
    assert len(cb.df) > 0
    assert cb.word_count is not None
