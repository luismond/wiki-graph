"""Wiki pages crawler."""

from random import shuffle
import numpy as np
from wiki_page import WikiPage
from db_util import get_pages_data, insert_autonym, \
    get_unsaved_autonym_page_ids
from __init__ import logger, MODEL, SEED_PAGE_NAME, SIM_THRESHOLD, LANG_CODES


class Crawler:
    def __init__(
        self,
        lang_code: str = 'en',
        max_pages: int = 50,
        max_new_pages: int = 50
        ):
        self.sim_threshold = SIM_THRESHOLD
        self.seed_page_name = SEED_PAGE_NAME
        self.max_pages = max_pages
        self.max_new_pages = max_new_pages
        self.lang_code = lang_code
        self.lang_codes = LANG_CODES
        self.autonym_lang_codes = None
        self.load()

    def set_autonym_lang_codes(self):
        self.autonym_lang_codes = [l for l in self.lang_codes \
                                   if l != self.lang_code]
        logger.info(f'Autonym lang codes: {self.autonym_lang_codes}')

    def load(self):
        """
        Initialize crawler with the seed page.

        - Save the page name.
        - Encode the seed paragraphs (todo: save them to vector db)
        """
        wp = WikiPage(self.seed_page_name, lang_code=self.lang_code)
        wp.save_page_name(sim_score=1.0)
        self.seed_paragraphs = wp.paragraphs
        self.seed_embedding = self.get_seed_embedding()
        logger.info(f'Loaded seed paragraphs from {self.seed_page_name}')

    def get_seed_embedding(self) -> np.ndarray:
        """
        Encode the seed paragraphs.
        This seed embedding will be used to determine the similarity
        of the new crawled pages.
        """
        seed_embedding = MODEL.encode(' '.join(self.seed_paragraphs))
        return seed_embedding

    def get_page_similarity_score(self, paragraphs: list) -> float:
        """
        Given a list of paragraphs, encode them and calculate
        their similarity against the seed.
        Args:
            paragraphs (list): A list of paragraphs.
        Returns:
            float: The similarity score between the paragraphs
            and the seed embedding.
        """
        paragraphs_embedding = MODEL.encode_document(' '.join(paragraphs))
        sim_score = float(MODEL.similarity(paragraphs_embedding,
                                           self.seed_embedding)[0])
        return sim_score

    def process_new_page(self, page_name):
        """
        Process a new Wikipedia page name: fetch the page,
        compute similarity score, save its metadata to the database.

        Args:
            page_name (str): The name of the new Wikipedia page to process.
        """
        wp_new = WikiPage(page_name, lang_code=self.lang_code)
        sim_score = self.get_page_similarity_score(wp_new.paragraphs)
        wp_new.save_page_name(sim_score)

    def crawl(self):
        logger.info(f'Crawling pages with similarity threshold '
                    f'{self.sim_threshold}')
        self.crawl_source_lang_pages()
        self.crawl_autonym_pages()
        logger.info('Crawling complete')

    def crawl_source_lang_pages(self):
        """
        Crawl Wikipedia pages based on a similarity threshold.
        - For each page name from DB, extract internal Wikipedia links
        (<a> inside <p> tags).
        - For every internal link not already saved, process it as a new page
        (fetch the content, compute similarity, save metadata).
        """
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
        """Populate the page_autonyms table and save autonym pages."""
        logger.info('populate_autonyms_table...')
        unsaved_pages = get_unsaved_autonym_page_ids(self.lang_code,
                                                     self.sim_threshold)
        n = 0
        for page_id, page_name in unsaved_pages:
            wp = WikiPage(page_name, self.lang_code)
            languages = wp.get_languages()
            if len(languages) == 0:
                continue
            for lang in languages:
                if not isinstance(lang, dict):
                    continue
                autonym = lang['key']
                lang_code = lang['code']
                if lang_code in self.autonym_lang_codes:

                    wp_x = WikiPage(page_name=autonym, lang_code=lang_code)
                    if len(wp_x.paragraphs) == 0:
                        continue
                    sim_score = self.get_page_similarity_score(wp_x.paragraphs)
                    wp_x.save_page_name(sim_score)
                    autonym_page_id = wp_x.page_id
                    insert_autonym(page_id, autonym,
                                   autonym_page_id, lang_code)
                    n += 1
        logger.info(f'Saved {n} autonyms')
