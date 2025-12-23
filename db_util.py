"""
Helper functions for database management.

Functionality includes DB and table creation, selection and insertion of
data such as pages, autonyms, links, paragraphs and embeddings.

"""

import sqlite3
import numpy as np
from __init__ import DB_NAME, logger


def create_tables():
    """Create the database using the DB_NAME from .env and the tables."""
    # Create a connection to a database file (will create if it doesn't exist)
    conn = sqlite3.connect(DB_NAME)
    logger.info(f'Connected to {DB_NAME}')

    # Create a cursor object to execute SQL commands
    cur = conn.cursor()

    # Create a pages table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            lang_code TEXT,
            url TEXT,
            crawled_at TEXT,
            sim_score REAL,
            UNIQUE(url)
        )
        '''
    )

    # Create a corpus table (paragraph text + embedding)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS paragraph_corpus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER REFERENCES pages(id),
            text TEXT,
            embedding BLOB,
            position INTEGER,
            UNIQUE(page_id, text)
        )
    ''')

    # Create a page_links table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS page_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_page_id INTEGER NOT NULL,
            target_page_id INTEGER NOT NULL,
            UNIQUE(source_page_id, target_page_id)
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS page_autonyms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER NOT NULL REFERENCES pages(id),
            autonym TEXT,
            lang_code TEXT,
            UNIQUE(autonym, lang_code)
        )
    ''')


def get_db_info():
    """Get database tables and number of rows in each."""
    conn = sqlite3.connect(DB_NAME)
    logger.info(f'Connected to {DB_NAME}')

    info = {}
    info['DB_NAME'] = DB_NAME
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    for table_tuple in tables:
        table = table_tuple[0]
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        info[table] = count
    conn.commit()
    conn.close()
    for i in info.items():
        logger.info(i)
    return info


def delete_table(name):
    """Delete a table."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(f'DROP TABLE IF EXISTS {name}')


# Data selecters/inserters

# pages
# todo: unify these page getters
def get_pages_data(sim_threshold, lang_code):
    """
    Retrieve page data with similarity above threshold and from lang code.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
    SELECT id, name, lang_code, sim_score FROM pages
    WHERE lang_code = ?
    AND sim_score >= ?
    """, (lang_code, sim_threshold)
    )
    pages = cur.fetchall()
    conn.close()
    logger.info(
        f'{len(pages)} page_names from pages table '
        f'with {lang_code} and {sim_threshold}'
        )
    return pages


def get_pages_table(sim_threshold):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
    SELECT id, name, lang_code, sim_score FROM pages
    WHERE sim_score >= ?
    """, (sim_threshold,))
    pages = cur.fetchall()
    logger.info(
        f'{len(pages)} page_ids in pages table '
        f'with sim_score > {sim_threshold}'
        )
    if len(pages) == 0:
        raise ValueError(f'No pages found with sim_threshold'
                         f' > {sim_threshold}')
    conn.close()
    return pages


def insert_page(page_name, lang_code, url, current_datetime_str, sim_score):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
    "INSERT OR IGNORE INTO pages "
    "(name, lang_code, url, crawled_at, sim_score) VALUES (?, ?, ?, ?, ?)",
    (page_name, lang_code, url, current_datetime_str, sim_score)
    )
    page_id = cur.lastrowid
    conn.commit()
    return page_id

# autonyms

def get_unsaved_autonym_page_ids(lang_code, sim_threshold):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, name FROM pages
        WHERE lang_code = ?
        AND sim_score >= ?
    """, (lang_code, sim_threshold))
    pages = cur.fetchall()
    
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT page_id FROM page_autonyms")
    page_autonyms_page_ids = [i[0] for i in set(cur.fetchall())]
    
    unsaved_pages =  set(i for i in pages if i[0] \
                         not in page_autonyms_page_ids)
    logger.info(f'{len(unsaved_pages)} unsaved page_ids in page_autonyms')
    return unsaved_pages


def insert_autonym(page_id, autonym, lang_code):
    """Insert autonym metadata to autonym table."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO page_autonyms "
        "(page_id, autonym, lang_code) VALUES (?, ?, ?)",
        (page_id, autonym, lang_code)
        )
    conn.commit()


# page links

def get_page_links_page_ids():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT source_page_id FROM page_links")
    links_page_ids = cur.fetchall()
    links_page_ids = set(p[0] for p in links_page_ids)
    logger.info(f'{len(links_page_ids)} page_ids in page_links table')
    return links_page_ids


def insert_page_link(source_page_id, target_page_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO page_links "
        "(source_page_id, target_page_id) VALUES (?, ?)",
        (source_page_id, target_page_id)
        )
    conn.commit()


def get_page_links_data(lang_code):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT pl.source_page_id, s_pages.name, s_pages.sim_score,
        pl.target_page_id, t_pages.name
        FROM page_links AS pl
        LEFT JOIN pages AS s_pages ON pl.source_page_id = s_pages.id
        LEFT JOIN pages AS t_pages ON pl.target_page_id = t_pages.id
        WHERE s_pages.lang_code = ?
    """, (lang_code,)
    )
    page_links = cur.fetchall()
    logger.info(f'Read {len(page_links)} page_links from page_links table')
    return page_links
    

# paragraphs

def insert_paragraph(page_id, paragraph, embedding, position):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO paragraph_corpus "
        "(page_id, text, embedding, position) VALUES (?, ?, ?, ?)",
        (page_id, paragraph, embedding, position)
    )
    conn.commit()
    
def get_paragraph_embeddings():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""SELECT embedding FROM paragraph_corpus""")
    embeddings = [np.frombuffer(e[0], dtype=np.float32) \
                  for e in cur.fetchall()]
    return embeddings
    

def get_paragraph_corpus():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT paragraph_corpus.id, page_id, pages.name, 
        text, position, pages.lang_code
        FROM paragraph_corpus
        LEFT JOIN pages ON paragraph_corpus.page_id = pages.id
    """)
    corpus = cur.fetchall()
    logger.info(f'Read paragraphs with {len(corpus)} rows')
    return corpus
   
 
def insert_page_metadata(page_name, lang_code, url, 
                         current_datetime_str, sim_score):
    """Save the page metadata in the pages table."""
    # todo: rename method to "save_page_metadata"
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
    "INSERT OR IGNORE INTO pages "
    "(name, lang_code, url, crawled_at, sim_score) "
    "VALUES (?, ?, ?, ?, ?)",
    (page_name, lang_code, url,
     current_datetime_str, sim_score)
    )
    page_id = cur.lastrowid
    conn.commit()
    return page_id