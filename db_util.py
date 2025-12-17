"""
Use this file to create the database and populate the tables.

sqlite 101:

# Insert a row of data
cur.execute("INSERT INTO users (name, age) VALUES (?, ?)", ("Alice", 30)

# Insert binary data
cur.execute("INSERT INTO soups (page_id, soup_data) VALUES (?, ?)", 
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
cur.execute("SELECT soup_data FROM soups WHERE page_id = ?", (page_id,))
row = cur.fetchone()
if row:
    unpickled_object = pickle.loads(row[0])

# remove a table
cur.execute('DROP TABLE IF EXISTS table_name')
"""

import sqlite3
from __init__ import DB_NAME, logger

def create_tables():
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
            UNIQUE(id, name, lang_code)
        )
        '''
    )

    # Create a paragraph_corpus table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS paragraphs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER,
            text TEXT,
            position INTEGER
        )
    ''')

    # Create a relationships table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS page_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_page_id INTEGER NOT NULL,
            target_page_id INTEGER NOT NULL,
            UNIQUE(source_page_id, target_page_id)
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS page_langs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER NOT NULL REFERENCES pages(id),
            langs TEXT
        )
    ''')

    # Create a soups table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS soups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER REFERENCES pages(id),
            soup_data BLOB
        ) 
    ''')

    # Create a paragraph embeddings table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS paragraph_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paragraph_id INTEGER REFERENCES paragraph_corpus(id),
            page_id INTEGER REFERENCES pages(id),
            embedding BLOB
        )
    ''')
    # Log database tables and number of rows in each
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cur.fetchall()
        for table_tuple in tables:
            table = table_tuple[0]
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                logger.info(f"Table '{table}': {count} rows")
            except Exception as e:
                logger.info(f"Could not count rows in table '{table}': {e}")
    except Exception as e:
        logger.info(f"Could not retrieve table list: {e}")
    conn.commit()
    conn.close()

