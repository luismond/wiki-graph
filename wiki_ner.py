"""Main wikiNER script."""

from __init__ import logger
from crawler import Crawler
from corpus_manager import CorpusManager


def main():
    logger.info('Starting main...')
    for _ in range(5):
        try:
            crawler = Crawler()
            crawler.crawl()
            cm = CorpusManager()
            cm.load()
        except Exception as e:
            logger.warning(str(e))
    logger.info('Finished main')


if __name__ == "__main__":
    main()
