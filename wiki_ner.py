"""Main wikiNER script."""

from __init__ import logger
from db_util import get_db_info
from crawler import Crawler
from corpus_manager import CorpusManager
from pages_graph import PagesGraph


def main():
    logger.info('Starting main...')
    for _ in range(2):
        try:
            get_db_info()
            crawler = Crawler(max_pages=15, max_new_pages=15)
            crawler.crawl()
            cm = CorpusManager()
            cm.load()
            pg = PagesGraph()
            pg.load()

        except Exception as e:
            logger.warning(str(e))
    logger.info('Finished main')


if __name__ == "__main__":
    main()
