"""Wiki pages crawler."""

import numpy as np
from random import shuffle
import sqlite3
from wiki_page import WikiPage
from nlp_utils import MODEL
from __init__ import logger, DB_NAME
from functools import cached_property

class Crawler:
    def __init__(
        self,
        sim_threshold: float,
        seed_page_name: str,
        lang_code: str = 'en'
        ):
        self.sim_threshold = sim_threshold
        self.seed_page_name = seed_page_name
        self.lang_code = lang_code
        self.load()
    
    def load(self):
        """
        Initialize crawler with the seed page.

        - Save the page name and soup
        - Encode the seed paragraphs (todo: save them to vector db)
        """
        wp = WikiPage(self.seed_page_name)
        wp.save_page_name(sim_score=1.0)
        wp.save_soup()

        self.seed_paragraphs = wp.paragraphs
        self.seed_embedding = self.get_seed_embedding()
        logger.info(f'Loaded seed paragraphs from {self.seed_page_name}')

    def get_seed_embedding(self) -> np.ndarray:
        """
        Encode the seed paragraphs.
        This seed embedding will be used to determine the similarity of the new crawled pages.
        """
        seed_embedding = MODEL.encode(' '.join(self.seed_paragraphs))
        return seed_embedding

    def get_page_similarity_score(self, paragraphs: list) -> float:
        """
        Given a list of paragraphs, encode them and calculate their similarity against the seed.
        Args:
            paragraphs (list): A list of paragraphs.
        Returns:
            float: The similarity score between the paragraphs and the seed embedding.
        """
        paragraphs_embedding = MODEL.encode_document(' '.join(paragraphs))
        sim_score = float(MODEL.similarity(paragraphs_embedding, self.seed_embedding)[0])
        return sim_score

    def process_new_page(self, page_name):
        """
        Process a new Wikipedia page name: fetch the page, compute similarity score,
        save its metadata to the database, and store its soup if the score meets the threshold.
        
        Args:
            page_name (str): The name of the new Wikipedia page to process.
        """
        wp_new = WikiPage(page_name, lang_code=self.lang_code)
        sim_score = self.get_page_similarity_score(wp_new.paragraphs)
        wp_new.save_page_name(sim_score)
        if sim_score >= self.sim_threshold:
            wp_new.save_soup()

    def get_page_names(self):
        """
        Retrieve page names with similarity above threshold.
        Shuffle the list of page names to randomize crawling order.
        """
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
        SELECT name FROM pages
        WHERE sim_score >= ?
        AND lang_code = ?
        """, (self.sim_threshold, self.lang_code)
        )
        page_names = [p[0] for p in cur.fetchall()]
        shuffle(page_names)
        conn.close()
        logger.info(f'Retrieved {len(page_names)} page_names from DB')
        return page_names

    def crawl(self):
        """
        Crawl Wikipedia pages based on a similarity threshold.
        - For each page name from DB, extract internal Wikipedia links (<a> inside <p> tags).
        - For every internal link not already saved, process it as a new page
        (fetch the content, compute similarity, save metadata and soup if threshold is met).
        """
        logger.info(f'Crawling pages with similarity threshold {self.sim_threshold}')
    
        page_names = self.get_page_names()

        visited = set()
        for page_name in page_names:

            wp = WikiPage(page_name=page_name, lang_code=self.lang_code)
            new_page_names = wp.get_internal_page_names()
            logger.info(new_page_names[:5])
            for new_page_name in new_page_names:
                if new_page_name in page_names + list(visited):
                    continue
                else:
                    self.process_new_page(new_page_name)
                    visited.add(new_page_name)
        


def main():
    logger.info(f'Starting main...')
    sim_threshold = .45
    for _ in range(2):
        crawler = Crawler(
            sim_threshold=sim_threshold,
            seed_page_name='Association_football'
            )
        crawler.crawl()
        sim_threshold *= .97
    logger.info(f'Finished main')


if __name__ == "__main__":
    main()
