from datetime import datetime

class FileLogger:
    def __init__(self):
        self.log_file = datetime.now().strftime("%Y%m%d_%H%M%S") + "_ProcLog.csv"
        with open(self.log_file, "a", encoding="utf-8") as f:
            if f.tell() == 0:
                f.write("timestamp, temp, time, ssr_res_state, ssr_fan_state, n_camp\n")

    def log(self, message):
        with open(self.log_file, "a", encoding="utf-8") as f:
            timestamp = datetime.now().isoformat()
            f.write(f"{timestamp},{message}")