import sqlite3

def main():
    # Create a connection to a database file (will create if it doesn't exist)
    conn = sqlite3.connect('uap_ent.db')

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

if __name__ == "__main__":
    main()
