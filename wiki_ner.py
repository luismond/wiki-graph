"""Main wikiNER script."""

import argparse
from __init__ import logger
from db_util import create_tables, get_db_info
from crawler import Crawler
from corpus_manager import CorpusManager
from pages_graph import PagesGraph


def main():
    """
    Main function to build the corpus.

    Usage:
        python wiki_ner.py --runs 10 --max-pages 10 --max-new-pages 10
    """
    logger.info('Starting main...')
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, required=True, default=5)
    ap.add_argument("--max-pages", type=int, required=True, default=5)
    ap.add_argument("--max-new-pages", type=int, required=True, default=5)
    args = ap.parse_args()
    logger.info(f'Runs: {args.runs}, max_pages: {args.max_pages}, '
                f'max_new_pages: {args.max_new_pages}')

    for n in range(args.runs):
        logger.info(f'Run {n}')
        try:
            create_tables()
            get_db_info()
            crawler = Crawler(max_pages=args.max_pages,
                              max_new_pages=args.max_new_pages)
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
