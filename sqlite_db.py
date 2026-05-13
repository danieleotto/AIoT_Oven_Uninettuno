import sqlite3, os
from customlib.functions import get_timestamp


class SQLiteDB:
    def __init__(self, filename:str) -> None:
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
            errore REAL,
            kp REAL,
            ki REAL,
            kd REAL,
            elapsedTime REAL,
            tempRate REAL,
            ssrRstate BOOLEAN,
            ssrFstate BOOLEAN,
            sysTemp REAL,
            resPower REAL
        )""")
        self.conn.commit()


    def add_sample(self, 
                   step:str, 
                   temp_target:float, 
                   temp_oven:float,
                   errore:float,
                   kp:float,
                   ki:float,
                   kd:float, 
                   elapsed_time:float, 
                   temp_rate:float, 
                   ssr_res_state:bool, 
                   ssr_fan_state:bool, 
                   sys_temp:float,
                   res_power:float) -> None:
        idproc = self.get_last_id("listaprocessi")
        self.cursor.execute(
            "INSERT INTO campioni (idproc, step, tempTarget, tempForno, errore, kp, ki, kd, elapsedTime, tempRate, ssrRstate, ssrFstate, sysTemp, resPower) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (idproc, step, temp_target, temp_oven, errore, kp, ki, kd, elapsed_time, temp_rate, ssr_res_state, ssr_fan_state, sys_temp, res_power)
        )
        self.conn.commit()


    def add_process(self, timestamp:str, processo:str) -> None:
        self.cursor.execute(
            "INSERT INTO listaprocessi (timestamp, processo) VALUES (?, ?)",
            (timestamp, processo)
        )
        self.conn.commit()
    
    
    def process_complete(self, duration:float, state:str) -> None:
        last_id = self.get_last_id("listaprocessi")
        self.cursor.execute(
            "UPDATE listaprocessi SET duration = ?, state = ? WHERE idProc = ?",
            (duration, state, last_id)
        )
        self.conn.commit()


    def read_all_samples(self) -> list:
        self.cursor.execute("SELECT * FROM campioni ORDER BY id ASC")
        return self.cursor.fetchall()
    
    
    def read_samples_by_id(self, id_proc:str) -> list:
        query = f"SELECT * FROM campioni WHERE idProc = {id_proc}"
        self.cursor.execute(query)
        return self.cursor.fetchall()


    def read_all_processes(self) -> list:
        self.cursor.execute("SELECT * FROM listaprocessi ORDER BY idProc ASC")
        return self.cursor.fetchall()


    def get_last_id(self, tablename:str) -> str | None:
        query = f"SELECT * FROM {tablename} ORDER BY 1 DESC LIMIT 1"
        self.cursor.execute(query)
        r = self.cursor.fetchone()
        return r[0] if r else None
    
    
    def log_samples(self) -> None:
        last_id = self.get_last_id("listaprocessi")
        if last_id is not None:
            LOG_FILE = get_timestamp(readable = True)+ f"_{last_id}_ProcessLog.csv"
            LOG_FILENAME = os.path.join(self.LOG_DIR, LOG_FILE)
            sample_list = self.read_samples_by_id(last_id)

            with open(LOG_FILENAME, "a", encoding="utf-8") as file:
                if file.tell() == 0:
                    file.write("id, idProc, step, tempTarget, tempForno, errore, kp, ki, kd, elapsedTime, tempRate, ssrRstate, ssrFstate, sysTemp, resPower\n")
                for sample in sample_list:
                    text_line = ",".join(str(value) for value in sample)
                    file.write(text_line + "\n")
        else:
            print("Valori non registrati, non esiste ID processo.")
    
    
    def log_processes(self) -> None:
        timestamp = get_timestamp(readable=True)
        LOG_FILE = timestamp + "_List.csv"
        LOG_FILENAME = os.path.join(self.LOG_DIR, LOG_FILE)
        process_list = self.read_all_processes()
        
        with open(LOG_FILENAME, "a", encoding="utf-8") as file:
            if file.tell() == 0:
                file.write("idProc, timestamp, processo, duration, state\n")
            for process in process_list:
                text_line = ",".join(str(value) for value in process)
                file.write(text_line + "\n")
