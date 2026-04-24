from datetime import datetime
import os

class FileLogger:
    def __init__(self):
        self.LOG_DIR = "logs"
        self.LOG_FILE = datetime.now().strftime("%Y%m%d-%H%M%S") + "_ProcLog.csv"
        self.LOG_FILENAME = os.path.join(self.LOG_DIR, self.LOG_FILE)
        os.makedirs(self.LOG_DIR, exist_ok=True)

        with open(self.LOG_FILENAME, "a", encoding="utf-8") as f:
            if f.tell() == 0:
                f.write("timestamp, idproc, processo, idsample, target, temp, etime, ssr_res_state, ssr_fan_state, systemp\n")

    def log(self, message):
        with open(self.LOG_FILENAME, "a", encoding="utf-8") as f:
            timestamp = datetime.now().isoformat()
            f.write(f"{timestamp},{message}")