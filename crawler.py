"""Wiki pages crawler."""

from random import shuffle
import numpy as np
from wiki_page import WikiPage
from db_util import get_pages_data, get_page_autonyms_data, insert_autonym
from __init__ import logger, MODEL, SEED_PAGE_NAME


class Crawler:
    def __init__(
        self,
        seed_page_name: str = SEED_PAGE_NAME,
        sim_threshold: float = 0.4,
        lang_code: str = 'en',
        max_pages: int = 50,
        max_new_pages: int = 50
        ):
        self.sim_threshold = sim_threshold
        self.seed_page_name = seed_page_name
        self.lang_code = lang_code
        self.max_pages = max_pages
        self.max_new_pages = max_new_pages
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

    def crawl(self):
        self.crawl_source_lang_pages()
        self.crawl_autonym_pages()

    def crawl_source_lang_pages(self):
        """
        Crawl Wikipedia pages based on a similarity threshold.
        - For each page name from DB, extract internal Wikipedia links (<a> inside <p> tags).
        - For every internal link not already saved, process it as a new page
        (fetch the content, compute similarity, save metadata and soup if threshold is met).
        """
        logger.info(f'Crawling pages with similarity threshold {self.sim_threshold}')

        page_data = get_pages_data(self.sim_threshold, self.lang_code)
        page_names = [p[1] for p in page_data]
        shuffle(page_data)
        visited = set()
        for _, page_name, _, _ in page_data[:self.max_pages]:
            wp = WikiPage(page_name=page_name, lang_code=self.lang_code)
            new_page_names = wp.get_internal_page_names()
            shuffle(new_page_names)
            for new_page_name in new_page_names[:self.max_new_pages]:
                if new_page_name in list(visited) + page_names:
                    continue
                self.process_new_page(new_page_name)
                visited.add(new_page_name)

    def crawl_autonym_pages(self):
        """
        - For each id from autonyms table, and given a x_lang code,
        - Fetch autonym page, save metadata and soup.
        """
        logger.info('Crawling autonyms')
        self.populate_autonyms_table()
        autonyms_data = get_page_autonyms_data()
        for _, _, _, autonym, lang_code in autonyms_data:
            wp_x = WikiPage(page_name=autonym, lang_code=lang_code)
            if len(wp_x.paragraphs) == 0:
                continue
            sim_score = self.get_page_similarity_score(wp_x.paragraphs)
            wp_x.save_page_name(sim_score)
            if sim_score >= self.sim_threshold:
                wp_x.save_soup()

    def populate_autonyms_table(self):
        """Use the page names in page table to populate the page_autonyms table."""
        logger.info('populate_autonyms_table...')
        pages = get_pages_data(sim_threshold=self.sim_threshold, lang_code=self.lang_code)
        # todo:
        # - assert that data insertion is efficient.
        # - assert that a 'not already saved' lookup is not needed.
        lang_codes = ['de', 'fr', 'pt', 'es', 'it']
        for page_id, page_name, _, _ in pages:
            wp = WikiPage(page_name=page_name, lang_code=self.lang_code)
            languages = wp.get_languages()
            if len(languages) == 0:
                continue
            for lang in languages:
                if not isinstance(lang, dict):
                    continue
                autonym = lang['key']
                lang_code = lang['code']
                if lang_code in lang_codes:
                    insert_autonym(page_id, autonym, lang_code)


def main():
    logger.info('Starting main...')
    sim_threshold = .45
    for _ in range(3):
        crawler = Crawler(
            sim_threshold=sim_threshold,
            seed_page_name='Association_football'
            )
        crawler.crawl()
        sim_threshold *= .97
    logger.info('Finished main')


if __name__ == "__main__":
    main()
