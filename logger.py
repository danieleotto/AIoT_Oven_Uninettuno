from datetime import datetime

class fileLogger:
    def __init__(self, log_file):
        self.log_file = log_file
        with open(log_file, "a") as f:
            if f.tell() == 0:
                f.write("timestamp, temp, time, n_camp\n")

    def log(self, temp, time, ssr_state, n_camp):
        with open(self.log_file, "a") as f:
            timestamp = datetime.now().isoformat()
            f.write(f"{timestamp},{temp:.2f},{time:.2f},{ssr_state},{n_camp}\n")