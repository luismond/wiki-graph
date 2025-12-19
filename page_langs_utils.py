"Utils to populate and read the page_autonyms table."

import pandas as pd
import sqlite3
from wiki_page import WikiPage
from db_util import get_pages_data
from __init__ import logger, DB_NAME


def populate_page_autonyms(sim_threshold, source_lang_code)-> pd.DataFrame:
    """Use the page names in page table to populate the page_autonyms table."""
    logger.info('Building page_autonyms corpus...')
    pages = get_pages_data(sim_threshold=sim_threshold, lang_code=source_lang_code)
    # todo: 
    # - assert that data insertion is efficient. 
    # - assert that a 'not already saved' lookup is not needed.
    lang_codes = ['de', 'fr', 'pt', 'es', 'it']
    for page_id, page_name, _, _ in pages:
        wp = WikiPage(page_name=page_name, lang_code=source_lang_code)
        languages = wp.get_languages()
        if len(languages) == 0:
            continue
        for lang in languages:
            if type(lang) is not dict:
                continue
            autonym = lang['key']
            lang_code = lang['code']
            if lang_code in lang_codes:
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                cur.execute(
                    "INSERT OR IGNORE INTO page_autonyms "
                    "(page_id, autonym, lang_code) VALUES (?, ?, ?)",
                    (page_id, autonym, lang_code)
                    )
                conn.commit()


