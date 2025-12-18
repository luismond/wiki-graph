"Temp file to bootstrap the solution to fetch autonym pages."
import json
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
    logger.info(f'Building page_langs corpus...')
    pages = get_pages(sim_threshold)

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT page_id FROM page_langs")
    langs_page_ids = cur.fetchall()
    langs_page_ids = set([p[0] for p in langs_page_ids])
    logger.info(f'{len(langs_page_ids)} page_ids in page_langs table')

    n = 0
    for page_id, page_name, _ in pages:
        if page_id not in langs_page_ids:# and sim_score >= sim_threshold:
            wp = WikiPage(page_name)
            languages = wp.get_languages()
            if len(languages) == 0:
                continue
            languages = json.dumps(languages)
            cur.execute(
                "INSERT INTO page_langs (page_id, langs) VALUES (?, ?)",
                (page_id, languages)
                )
            conn.commit()
            n += 1
    logger.info(f'Added {n} page_langs')


def read_page_langs() -> pd.DataFrame:
    """Read the page_langs data."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT page_langs.page_id, pages.name, page_langs.langs
        FROM page_langs
        LEFT JOIN pages ON page_langs.page_id = pages.id
    """)
    page_langs = cur.fetchall()
    page_langs = [(page_id, name, json.loads(langs)) for (page_id, name, langs) in page_langs]
    columns = ['page_id', 'name', 'langs']
    df = pd.DataFrame(page_langs, columns=columns)
    logger.info(f'Read {len(df)} from page_langs table')
    return df


def get_target_page_name(langs_list: list, x_lang: str):
    for d in langs_list:
        if d['code'] == x_lang:
            return d['key']
       