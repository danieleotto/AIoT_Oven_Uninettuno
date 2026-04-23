import sqlite3

class SQLite3DB:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
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