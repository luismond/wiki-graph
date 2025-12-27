"""
Helper functions for database management.

Functionality includes:
    - Database and table creation
    - Selection and insertion of data:
        - Pages, autonyms, page links, paragraphs and embeddings).
"""

import sqlite3
from __init__ import DB_NAME, logger


def create_tables():
    """Create the database using the DB_NAME from .env and the tables."""
    # Create a connection to a database file (will create if it doesn"t exist)
    conn = sqlite3.connect(DB_NAME)
    logger.info(f"Connected to {DB_NAME}")

    # Create a cursor object to execute SQL commands
    cur = conn.cursor()

    # Create a pages table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            lang_code TEXT,
            url TEXT,
            crawled_at TEXT,
            sim_score REAL,
            UNIQUE(url)
            )
        """
        )

    # Create a paragraph corpus table (paragraph text + embedding)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS paragraph_corpus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER REFERENCES pages(id),
            text TEXT,
            embedding BLOB,
            position INTEGER,
            UNIQUE(page_id, text)
            )
        """
        )

    # Create a page_links table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS page_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_page_id INTEGER NOT NULL,
            target_page_id INTEGER NOT NULL,
            UNIQUE(source_page_id, target_page_id)
            )
        """
        )

    # Create a page_autonyms table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS page_autonyms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_page_id INTEGER NOT NULL REFERENCES pages(id),
            autonym TEXT,
            autonym_page_id INTEGER NOT NULL REFERENCES pages(id),
            lang_code TEXT,
            UNIQUE(autonym, lang_code)
            )
        """
        )


def delete_table(name):
    """Delete a table."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        f"""
        DROP TABLE IF EXISTS {name}
        """
        )


def get_db_info() -> dict:
    """Get database tables and number of rows in each."""
    conn = sqlite3.connect(DB_NAME)
    logger.info(f"Connected to {DB_NAME}")
    info = {}
    info["DB_NAME"] = DB_NAME
    cur = conn.cursor()
    cur.execute(
        """
        SELECT name FROM sqlite_master WHERE type="table";
        """
        )
    tables = cur.fetchall()
    for table_tuple in tables:
        table = table_tuple[0]
        cur.execute(
            f"""
            SELECT COUNT(*) FROM {table}
            """
            )
        count = cur.fetchone()[0]
        info[table] = count
    conn.commit()
    conn.close()
    for i in info.items():
        logger.info(i)
    return info


# pages

def get_pages_data(sim_threshold: float, lang_code: str) -> list:
    """
    Retrieve page data with similarity above threshold and from lang code.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, name, lang_code, sim_score FROM pages
        WHERE lang_code = ?
        AND sim_score >= ?
        """, (lang_code, sim_threshold)
        )
    pages = cur.fetchall()
    conn.close()
    logger.info(
        f"{len(pages)} page_names from pages table "
        f"with {lang_code} and {sim_threshold}"
        )
    return pages


def insert_page_metadata(page_name: str, lang_code: str, url: str,
                         current_datetime_str: str, sim_score: float) -> int:
    """Save the page metadata in the pages table."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO pages
        (name, lang_code, url, crawled_at, sim_score)
        VALUES (?, ?, ?, ?, ?)
        """, (page_name, lang_code, url, current_datetime_str, sim_score)
        )
    page_id = cur.lastrowid
    conn.commit()
    return page_id


# page_autonyms

def get_unsaved_autonym_page_ids(lang_code: str, sim_threshold: float) -> list:
    """
    Retrieve unsaved autonym page IDs and names for a given language code
    and minimum similarity threshold.

    This function selects all page IDs and names from the pages table that
    match the provided language code and have a sim_score above or equal
    to the specified threshold. It then returns only those page IDs and
    names that do not already exist as source_page_id in the page_autonyms
    table.

    Args:
        lang_code (str): Language code (e.g., 'fr', 'de', etc.).
        sim_threshold (float): Minimum similarity score required.

    Returns:
        list: List of (id, name) tuples where each page ID has not yet
              been added to the page_autonyms table.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, name FROM pages
        WHERE lang_code = ?
        AND sim_score >= ?
        """, (lang_code, sim_threshold)
        )
    pages = cur.fetchall()

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT source_page_id FROM page_autonyms
        """
        )
    page_autonyms_page_ids = [i[0] for i in set(cur.fetchall())]
    unsaved_pages =  set(i for i in pages if i[0] \
                         not in page_autonyms_page_ids)
    logger.info(f"{len(unsaved_pages)} unsaved page_ids in page_autonyms")
    return unsaved_pages


def read_autonyms_data(tgt_lang: str) -> list:
    """
    Select the autonym data, join the source page name
    and filter by autonym language.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT pages.name, a.source_page_id, a.autonym,
           a.autonym_page_id, a.lang_code
        FROM page_autonyms as a
        LEFT JOIN pages ON pages.id = a.source_page_id
        WHERE a.lang_code = ?
        """, (tgt_lang,)
        )
    result = cur.fetchall()
    return result


def insert_autonym(page_id: int, autonym: str, autonym_page_id: int, lang_code: str):
    """Insert autonym metadata to autonym table."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO page_autonyms
        (source_page_id, autonym, autonym_page_id, lang_code)
        VALUES (?, ?, ?, ?)
        """, (page_id, autonym, autonym_page_id, lang_code)
        )
    conn.commit()


# page_links

def get_page_links_page_ids() -> set:
    """
    Retrieve a set of all unique source_page_id values from the page_links table.

    Returns:
        set: A set containing all distinct source_page_id values found in the
            page_links table.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT source_page_id FROM page_links
        """
        )
    links_page_ids = cur.fetchall()
    links_page_ids = set(p[0] for p in links_page_ids)
    logger.info(f"{len(links_page_ids)} page_ids in page_links table")
    return links_page_ids


def insert_page_link(source_page_id: int, target_page_id: int):
    """
    Insert a record into the page_links table.

    Args:
        source_page_id (int): The page ID of the source page.
        target_page_id (int): The page ID of the target page.

    This function adds a directed link from the source to the target page
    in the page_links table.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO page_links
        (source_page_id, target_page_id) VALUES (?, ?)
        """, (source_page_id, target_page_id)
        )
    conn.commit()


def get_page_links_data(lang_code: str) -> list:
    """
    Get the source/target page links data and join the page names
    for visualization.

    Returns:
        A list of tuples, for example:
            (source_page_id, source_page_name, source_page_sim_score,
             target_page_id, target_page_name)
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT pl.source_page_id, s_pages.name, s_pages.sim_score,
        pl.target_page_id, t_pages.name
        FROM page_links AS pl
        LEFT JOIN pages AS s_pages ON pl.source_page_id = s_pages.id
        LEFT JOIN pages AS t_pages ON pl.target_page_id = t_pages.id
        WHERE s_pages.lang_code = ?
        """, (lang_code,)
        )
    page_links = cur.fetchall()
    logger.info(f"Read {len(page_links)} page_links from page_links table")
    return page_links


# paragraph_corpus

def insert_paragraph(page_id: int, paragraph: str, embedding: bytes, position: int):
    """
    Insert a paragraph and its embedding into the paragraph_corpus table.

    Args:
        page_id (int): The id of the page the paragraph belongs to.
        paragraph (str): The text of the paragraph.
        embedding (bytes): The paragraph embedding as a BLOB.
        position (int): The position of the paragraph within the page.

    This inserts a record into the paragraph_corpus table if not already 
    present, based on the unique (page_id, text) constraint.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR IGNORE INTO paragraph_corpus
        (page_id, text, embedding, position) VALUES (?, ?, ?, ?)
        """, (page_id, paragraph, embedding, position)
        )
    conn.commit()


def get_paragraph_embeddings() -> list:
    """
    Retrieve all paragraph embeddings from the paragraph_corpus table.

    Returns:
        list: A list of tuples, where each tuple contains a single element
        representing the paragraph embedding as stored in the database.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT embedding FROM paragraph_corpus
        """
        )
    return cur.fetchall()


def get_paragraph_corpus() -> list:
    """
    Retrieve the full paragraph corpus including page and language info.

    Returns:
        list: Each tuple contains
            (paragraph_corpus.id, page_id, page name, paragraph text,
            position, lang_code). One tuple per paragraph in the corpus.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT paragraph_corpus.id, page_id, pages.name,
        text, position, pages.lang_code
        FROM paragraph_corpus
        LEFT JOIN pages ON paragraph_corpus.page_id = pages.id
        """
        )
    corpus = cur.fetchall()
    logger.info(f"Read paragraphs with {len(corpus)} rows")
    return corpus


def get_paragraphs_by_page_id(page_id: int) -> str:
    """
    Retrieve the concatenated paragraph text for a given page_id.

    Args:
        page_id (int): The ID of the page whose paragraphs are requested.

    Returns:
        str or None: All paragraphs (joined by '\n') for the specified page_id,
        or None if no paragraphs are found.
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT text, position
        FROM paragraph_corpus
        WHERE page_id = ?
        """, (page_id,)
        )
    pgfs = cur.fetchall()
    pgfs = [i[0] for i in sorted(pgfs, key=lambda i: i[1])]
    if pgfs:
        return "\n".join(pgfs)
    return None
