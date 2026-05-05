import sqlite3, os
from datetime import datetime

class SQLite3DB:
    def __init__(self, filename):
        self.DB_DIR = "database"
        self.DB_FILE = os.path.join(self.DB_DIR, filename)
        os.makedirs(self.DB_DIR, exist_ok=True)
        
        self.LOG_DIR = "logs"
        os.makedirs(self.LOG_DIR, exist_ok=True)

        self.conn = sqlite3.connect(self.DB_FILE)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS listaprocessi (
            idProc INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            processo TEXT,
            duration REAL,
            state TEXT
        )""")
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS campioni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idProc INTEGER,
            step TEXT,
            tempTarget REAL,
            tempForno REAL,
            elapsedTime REAL,
            tempRate REAL,
            ssrRstate BOOLEAN,
            ssrFstate BOOLEAN,
            sysTemp REAL
        )""")
        self.conn.commit()

    def addSample(self, step, temptarget, tempoven, elapsedtime, temprate, ssr1state, ssr2state, sysTemp):
        idproc = self.getLastId("listaprocessi")
        self.cursor.execute(
            "INSERT INTO campioni (idproc, step, tempTarget, tempForno, elapsedTime, tempRate, ssrRstate, ssrFstate, sysTemp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (idproc, step, temptarget, tempoven, elapsedtime, temprate, ssr1state, ssr2state, sysTemp)
        )
        self.conn.commit()

    def addProcess(self, timestamp, processo):
        self.cursor.execute(
            "INSERT INTO listaprocessi (timestamp, processo) VALUES (?, ?)",
            (timestamp, processo)
        )
        self.conn.commit()
    
    def processComplete(self, duration, state):
        lastId = self.getLastId("listaprocessi")
        self.cursor.execute(
            "UPDATE listaprocessi SET duration = ?, state = ? WHERE idProc = ?",
            (duration, state, lastId)
        )
        self.conn.commit()

    def readAllSamples(self):
        self.cursor.execute("SELECT * FROM campioni ORDER BY id ASC")
        return self.cursor.fetchall()
    
    def readSamplesByIdProc(self, idProc):
        query = f"SELECT * FROM campioni WHERE idProc = {idProc}"
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def readAllProcesses(self):
        self.cursor.execute("SELECT * FROM listaprocessi ORDER BY idProc ASC")
        return self.cursor.fetchall()

    def getLastId(self, tablename):
        query = f"SELECT * FROM {tablename} ORDER BY 1 DESC LIMIT 1"
        self.cursor.execute(query)
        r = self.cursor.fetchone()
        return r[0] if r else None
    
    def logSamples(self):
        last_id = self.getLastId("listaprocessi")
        query = f"SELECT timestamp FROM listaprocessi WHERE idProc = {last_id}"
        self.cursor.execute(query)
        timeStamp = self.cursor.fetchone()[0]
        LOG_FILE = str(timeStamp) + f"_{last_id}_ProcessLog.csv"
        LOG_FILENAME = os.path.join(self.LOG_DIR, LOG_FILE)
        sampleList = self.readSamplesByIdProc(last_id)
        
        with open(LOG_FILENAME, "a", encoding="utf-8") as file:
            if file.tell() == 0:
                file.write("id, idProc, step, tempTarget, tempForno, elapsedTime, tempRate, ssrRstate, ssrFstate, sysTemp\n")
            for sample in sampleList:
                textLine = ",".join(str(value) for value in sample)
                file.write(textLine + "\n")
    
    def logProcesses(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        LOG_FILE = str(timestamp) + "_List.csv"
        LOG_FILENAME = os.path.join(self.LOG_DIR, LOG_FILE)
        processList = self.readAllProcesses()
        
        with open(LOG_FILENAME, "a", encoding="utf-8") as file:
            if file.tell() == 0:
                file.write("idProc, timestamp, processo, duration, state\n")
            for process in processList:
                textLine = ",".join(str(value) for value in process)
                file.write(textLine + "\n")