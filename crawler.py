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


    @cached_property
    def seed_paragraphs(self):
        """Retrieve the paragraphs of an initial set of pages."""
        seed_page_wp = WikiPage(self.seed_page_name)
        seed_page_wp.save_page_name(sim_score=1.0)
        paragraphs = seed_page_wp.paragraphs
        logger.info(f'Loaded seed paragraphs from {self.seed_page_name}')
        return paragraphs

    @cached_property
    def seed_embedding(self) -> np.ndarray:
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

    def process_new_page_name(self, new_page_name, sim_score):
        """
        Process a new Wikipedia page name: fetch the page, compute similarity score,
        save its metadata to the database, and store its soup if the score meets the threshold.
        
        Args:
            new_page_name (str): The name of the new Wikipedia page to process.
            sim_score (float): The similarity score between the paragraphs and the seed embedding.
        """
        wp_new = WikiPage(new_page_name, lang=self.lang_code)
        sim_score = self.get_page_similarity_score(wp_new.paragraphs)
        wp_new.save_page_name(sim_score)
        if sim_score >= self.sim_threshold:
            wp_new.save_soup()

    def crawl(self):
        """
        Crawl Wikipedia pages based on a similarity threshold.
            - Connect to the database and retrieves all pages.
            - Shuffle the list of page names to randomize crawling order.
            - Iterate through each page whose similarity score is above 0.4.
            - For each such page, extract internal Wikipedia page links (<a> inside <p> tags).
            - For every internal link not already in the database, processe it as a new page
            (fetch, compute similarity, save metadata and soup if threshold is met).

        Args:
            sim_threshold (float): The similarity threshold above which a page is saved.
        """
        logger.info(f'Crawling pages with similarity threshold {self.sim_threshold}')
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
        SELECT id, name, sim_score FROM pages
        WHERE sim_score >= ?
        """, (self.sim_threshold,)
        )
        pages = cur.fetchall()
        page_names = [name for _, name, _ in pages]
        shuffle(page_names)

        visited = set()
        n = 0
        for _, name, sim_score in pages:
            wp = WikiPage(name)
            new_page_names = wp.get_internal_page_names()
            for new_page_name in new_page_names:
                if new_page_name in page_names + list(visited):
                    continue
                else:
                    self.process_new_page_name(new_page_name, sim_score)
                    n += 1
                    visited.add(new_page_name)
        logger.info(f'Processed {n} new pages')
        conn.close()


def main():
    logger.info(f'Starting main...')
    sim_threshold = .45
    for _ in range(20):
        crawler = Crawler(
            sim_threshold=sim_threshold,
            seed_page_name='Association_football'
            )
        crawler.crawl()
        sim_threshold *= .97
    logger.info(f'Finished main')


if __name__ == "__main__":
    main()
