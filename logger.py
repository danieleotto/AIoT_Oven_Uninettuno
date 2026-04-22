from datetime import datetime

class fileLogger:
    def __init__(self, log_file):
        self.log_file = log_file
        with open(log_file, "a") as f:
            if f.tell() == 0:
                f.write("timestamp, temp, time\n")

    def log(self, temp, time):
        with open(self.log_file, "a") as f:
            timestamp = datetime.now().isoformat()
            f.write(f"{timestamp},{temp:.2f},{time:.2f}\n")

