"""Main wikiNER script."""

from __init__ import logger
from crawler import Crawler
from corpus_manager import CorpusManager
from relationship_builder import RelationshipBuilder
from network_visualizer import draw_graph_pyvis

def main():
    logger.info('Starting main...')
    for _ in range(2):
        try:
            crawler = Crawler(max_pages=10, max_new_pages=10)
            crawler.crawl()
            cm = CorpusManager()
            cm.load()
            rlb = RelationshipBuilder()
            rlb.build_page_links()
            dfr = rlb.read_page_links()
            dfx = rlb.filter(dfr)
            draw_graph_pyvis(dfx)

        except Exception as e:
            logger.warning(str(e))
    logger.info('Finished main')


if __name__ == "__main__":
    main()
