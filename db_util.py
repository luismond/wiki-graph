import os
import sqlite3
import pickle

conn = sqlite3.connect('uap_ent.db')

def main():
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
        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_page_id INTEGER,
            target TEXT,
            target_type TEXT
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


if __name__ == "__main__":
    main()
