"""Wiki pages crawler."""

from random import shuffle
import numpy as np
from wiki_page import WikiPage
from db_util import get_pages_data, get_page_autonyms_data, populate_page_autonyms
from __init__ import logger, MODEL


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
        wp = WikiPage(self.seed_page_name, lang_code=self.lang_code)
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

    def crawl(self, max_pages: int = 50, max_new_pages: int = 50):
        """
        Crawl Wikipedia pages based on a similarity threshold.
        - For each page name from DB, extract internal Wikipedia links (<a> inside <p> tags).
        - For every internal link not already saved, process it as a new page
        (fetch the content, compute similarity, save metadata and soup if threshold is met).
        """
        logger.info(f'Crawling pages with similarity threshold {self.sim_threshold}')

        page_data = get_pages_data(self.sim_threshold, self.lang_code)[:max_pages]
        shuffle(page_data)
        visited = set()
        for _, page_name, _, _ in page_data:
            wp = WikiPage(page_name=page_name, lang_code=self.lang_code)
            new_page_names = wp.get_internal_page_names()
            shuffle(new_page_names)
            for new_page_name in new_page_names[:max_new_pages]:
                if new_page_name in visited:
                    continue
                self.process_new_page(new_page_name)
                visited.add(new_page_name)
        self.crawl_autonyms()

    def crawl_autonyms(self):
        """
        - For each id from autonyms table, and given a x_lang code,
        - Fetch autonym page, save metadata and soup.
        """
        logger.info('Crawling autonyms')
        populate_page_autonyms(
            sim_threshold=self.sim_threshold,
            source_lang_code=self.lang_code
            )
        autonyms_data = get_page_autonyms_data()
        for _, _, _, autonym, lang_code in autonyms_data:
            wp_x = WikiPage(page_name=autonym, lang_code=lang_code)
            if len(wp_x.paragraphs) == 0:
                continue
            sim_score = self.get_page_similarity_score(wp_x.paragraphs)
            wp_x.save_page_name(sim_score)
            wp_x.save_soup()


def main():
    logger.info('Starting main...')
    sim_threshold = .45
    for _ in range(2):
        crawler = Crawler(
            sim_threshold=sim_threshold,
            seed_page_name='Association_football'
            )
        crawler.crawl()
        sim_threshold *= .97
    logger.info('Finished main')


if __name__ == "__main__":
    main()
