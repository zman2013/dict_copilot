import sqlite3

DATABASE = 'words.db'

def init_db():
    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        # We add columns for phonetic, translation and audio_link
        cur.execute("""
            CREATE TABLE IF NOT EXISTS words (
                word TEXT PRIMARY KEY,
                phonetic TEXT,
                translation TEXT,
                audio_link TEXT,
                date TEXT
            )
        """)
        con.commit()

init_db()
