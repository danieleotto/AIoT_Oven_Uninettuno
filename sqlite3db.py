import sqlite3

class SQLite3DB:
    def __init__(self):
        self.conn = sqlite3.connect("sqlite.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS stato (id INTEGER, timestamp TEXT, elapsedTime REAL, temperatura REAL, ssr1state BOOLEAN, ssr2state BOOLEAN)")

    def add(self, idstate, timestamp, elapsedtime, temperatura, ssr1state, ssr2state):
        self.cursor.execute("INSERT INTO stato (?, ?, ?, ?, ? ?)", (idstate, timestamp, elapsedtime, temperatura, ssr1state, ssr2state))
        self.conn.commit()

