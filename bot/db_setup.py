import sqlite3
from sqlite3 import Error

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect("./db/petitions.db")
    except Error as e:
        print(e)
    return conn

def create_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS petitions (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    duration INTEGER NOT NULL,
                    status TEXT DEFAULT 'open',
                    yes_votes INTEGER DEFAULT 0,
                    no_votes INTEGER DEFAULT 0
                  );""")

    except Error as e:
        print(e)

def main():
    conn = create_connection()
    if conn is not None:
        create_table(conn)

if __name__ == "__main__":
    main()
