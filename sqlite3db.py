import sqlite3, os

class SQLite3DB:
    def __init__(self, filename):
        self.DB_DIR = "database"
        self.DB_FILE = os.path.join(self.DB_DIR, filename)

        os.makedirs(self.DB_DIR, exist_ok=True)

        self.conn = sqlite3.connect(self.DB_FILE)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS stato (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            elapsedTime REAL,
            temperatura REAL,
            ssrRstate BOOLEAN,
            ssrFstate BOOLEAN
        )""")
        self.conn.commit()

    def add(self, timestamp, elapsedtime, temperatura, ssr1state, ssr2state):
        self.cursor.execute(
            "INSERT INTO stato (timestamp, elapsedTime, temperatura, ssrRstate, ssrFstate)VALUES (?, ?, ?, ?, ?)",
            (timestamp, elapsedtime, temperatura, ssr1state, ssr2state)
        )
        self.conn.commit()

    def readAll(self):
        self.cursor.execute("SELECT * FROM stato ORDER BY id ASC")
        return self.cursor.fetchall()