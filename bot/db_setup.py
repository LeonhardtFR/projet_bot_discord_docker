import sqlite3
from sqlite3 import Error


import os

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
                        status TEXT NOT NULL DEFAULT 'open',
                        created_at TIMESTAMP NOT NULL,
                        yes_votes INTEGER NOT NULL DEFAULT 0,
                        no_votes INTEGER NOT NULL DEFAULT 0
                  );""")
        
        # Ajouter la création de la table votes
        cursor.execute("""CREATE TABLE IF NOT EXISTS votes (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        petition_id INTEGER NOT NULL,
                        vote TEXT NOT NULL,
                        FOREIGN KEY (petition_id) REFERENCES petitions (id)
                  );""")

    except Error as e:
        print(e)


def main():
    conn = create_connection()
    if conn is not None:
        create_table(conn)

if __name__ == "__main__":
    main()
