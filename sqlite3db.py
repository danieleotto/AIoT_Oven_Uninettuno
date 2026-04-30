import sqlite3, os

class SQLite3DB:
    def __init__(self, filename):
        self.DB_DIR = "database"
        self.DB_FILE = os.path.join(self.DB_DIR, filename)

        os.makedirs(self.DB_DIR, exist_ok=True)

        self.conn = sqlite3.connect(self.DB_FILE)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS listaprocessi (
            idProc INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            processo TEXT
        )""")
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS campioni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idProc INTEGER,
            tempTarget REAL,
            tempForno REAL,
            elapsedTime REAL,
            tempRate REAL,
            ssrRstate BOOLEAN,
            ssrFstate BOOLEAN,
            tempSystem REAL
        )""")
        self.conn.commit()

    def addSample(self, idproc, temptarget, tempoven, elapsedtime, temprate, ssr1state, ssr2state, tempsystem):
        self.cursor.execute(
            "INSERT INTO campioni (idproc, tempTarget, tempForno, elapsedTime, tempRate, ssrRstate, ssrFstate, tempSystem) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (idproc, temptarget, tempoven, elapsedtime, temprate, ssr1state, ssr2state, tempsystem)
        )
        self.conn.commit()

    def addProcess(self, timestamp, processo):
        self.cursor.execute(
            "INSERT INTO listaprocessi (timestamp, processo) VALUES (?, ?)",
            (timestamp, processo)
        )
        self.conn.commit()

    def readSamples(self):
        self.cursor.execute("SELECT * FROM campioni ORDER BY id ASC")
        return self.cursor.fetchall()

    def readProcesses(self):
        self.cursor.execute("SELECT * FROM listaprocessi ORDER BY idProc ASC")
        return self.cursor.fetchall()

    def getLastId(self, tablename):
        query = f"SELECT * FROM {tablename} ORDER BY 1 DESC LIMIT 1"
        self.cursor.execute(query)
        r = self.cursor.fetchone()
        return r[0] if r else None