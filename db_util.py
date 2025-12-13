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

import os
import sqlite3
import pandas as pd

conn = sqlite3.connect('uap_ent.db')

def create_tables():
    # Create a connection to a database file (will create if it doesn't exist)
    
    # Create a cursor object to execute SQL commands
    cur = conn.cursor()

    # Create a pages table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            url TEXT,
            crawled_at TEXT,
            sim_score REAL
        )
    ''')

    # Create a paragraph_corpus table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS paragraph_corpus (
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

   # Create a soups table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS soups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER,
            soup_data BLOB
        )
    ''')


def populate_soups_table():
    # Read all pages from the pages table
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM pages")
    pages = cur.fetchall()  # list of (id, name)

    soups_path = 'data/soups'
    for page_id, page_name in pages:
        if page_name:
            soup_file = os.path.join(soups_path, page_name + '.pkl')
            if os.path.exists(soup_file):
                with open(soup_file, 'rb') as f:
                    pickled_data = f.read()
                cur.execute("INSERT INTO soups (page_id, soup_data) VALUES (?, ?)", 
                            (page_id, sqlite3.Binary(pickled_data)))
    conn.commit()


def build_page_table():
    df = pd.read_csv('data/pages.tsv', sep='\t')
    df.shape
    df.sample(10).head()

    # `pages`: id (PK), name (unique), url, crawled_at, sim_score
    # Create a connection to a database file (will create if it doesn't exist)
    conn = sqlite3.connect('uap_ent.db')

    # Create a cursor object to execute SQL commands
    cur = conn.cursor()
    for _, row in df.iterrows():
        cur.execute(
            "INSERT INTO pages (name, url, crawled_at, sim_score) VALUES (?, ?, ?, ?)",
            (row['name'], row['url'], row['crawled_at'], row['sim_score'])
            )
    conn.commit()


if __name__ == "__main__":
    main()
