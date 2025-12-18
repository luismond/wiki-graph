"Temp file to bootstrap the solution to fetch autonym pages."

import pandas as pd
import sqlite3
from wiki_page import WikiPage
from __init__ import logger, DB_NAME


def get_pages(sim_threshold):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
    SELECT id, name, sim_score FROM pages
    WHERE sim_score >= ?
    """, (sim_threshold,))
    pages = cur.fetchall()
    logger.info(f'{len(pages)} page_ids in pages table with sim_score > {sim_threshold}')
    if len(pages) == 0:
        raise ValueError(f'No pages found with sim_score > {sim_threshold}')
    conn.close()
    return pages


def populate_page_langs(sim_threshold)-> pd.DataFrame:
    """Use the page names in page table to populate the page_langs table."""
    logger.info(f'Building page_autonyms corpus...')
    lang_codes = ['de', 'fr', 'pt', 'es', 'it']
    pages = get_pages(sim_threshold)

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT page_id FROM page_autonyms")
    langs_page_ids = cur.fetchall()
    langs_page_ids = set([p[0] for p in langs_page_ids])
    logger.info(f'{len(langs_page_ids)} page_ids in page_autonyms table')

    n = 0
    for page_id, page_name, _ in pages:
        if page_id not in langs_page_ids:# and sim_score >= sim_threshold:
            wp = WikiPage(page_name)
            languages = wp.get_languages()
            if len(languages) == 0:
                continue
            for lang in languages:
                autonym = lang['key']
                lang_code = lang['code']
                if lang_code in lang_codes:
                    cur.execute(
                        "INSERT INTO page_autonyms (page_id, autonym, lang_code) VALUES (?, ?, ?)",
                        (page_id, autonym, lang_code)
                        )
                    conn.commit()
                    n += 1
    logger.info(f'Added {n} autonyms')


def read_page_langs() -> pd.DataFrame:
    """Read the page_autonyms data."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT page_autonyms.id, page_autonyms.page_id, pages.name, page_autonyms.autonym, page_autonyms.lang_code
        FROM page_autonyms
        LEFT JOIN pages ON page_autonyms.page_id = pages.id
    """)
    page_langs = cur.fetchall()
    return page_langs


def to_df(page_langs):
    columns = ['id', 'page_id', 'name', 'autonym', 'lang_code']
    df = pd.DataFrame(page_langs, columns=columns)
    logger.info(f'Read {len(df)} from page_langs table')
    return df
