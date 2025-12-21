"""
Use this file to create the database and populate the tables.

sqlite 101:

# Insert a row of data
cur.execute("INSERT INTO users (name, age) VALUES (?, ?)", ("Alice", 30)

# Insert binary data
cur.execute("INSERT INTO pages (page_id, page_data) VALUES (?, ?)",
            (page_id, sqlite3.Binary(pickled_data)))

# Commit the transaction
conn.commit(

# Query data
cur.execute("SELECT * FROM users")
rows = cur.fetchall()
print(rows)  # Output: [(1, 'Alice', 30)

# Close the connection
conn.close()

# Query one data item
cur.execute("SELECT page_data FROM pages WHERE page_id = ?", (page_id,))
row = cur.fetchone()
if row:
    unpickled_object = pickle.loads(row[0])

# remove a table
cur.execute('DROP TABLE IF EXISTS table_name')
"""

import sqlite3
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


def get_page_autonyms_data():
    """Read the page_autonyms data."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT page_autonyms.id, page_autonyms.page_id, pages.name, 
        page_autonyms.autonym, page_autonyms.lang_code
        FROM page_autonyms
        LEFT JOIN pages ON page_autonyms.page_id = pages.id
    """)
    return cur.fetchall()


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
