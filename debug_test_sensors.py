from MAX6675lib import MAX6675
import json, time, sys

with open("config.json") as configFile:
    configData = json.load(configFile)
    
TC_SCK = configData["TC_PIN_SCK"]
TC_CS = configData["TC_PIN_CS"]
TC_DO = configData["TC_PIN_DO"]
interval = configData["sample_interval"]
sample_size = configData["avg_sample_size"]

tc = MAX6675(TC_SCK,TC_CS,TC_DO, sample_size)

startTime = lastTime = time.time()
temp = t = 0
try:
    tc.buffer.clear()
    print(f"Buffer: {tc.buffer}  |  LastTemp: {t}  | LastAVG: {temp}")
    time.sleep(1)
    print(f"Inizializzazione sonda.\nEseguo {tc.sample_size} letture con intervallo 1 s.\n")
    while len(tc.buffer) != tc.sample_size:
        for i in range(1,tc.sample_size + 1):
            t = tc.readTempC_average()
            time.sleep(0.3)
            sys.stdout.write("\033[F\033[K")
            sys.stdout.write("\033[F\033[K")
            text = "* " * i + "  " * (tc.sample_size - i)
            print(f"{text} {i}/{tc.sample_size}")
            print(f"Buffer: {tc.buffer}  |  LastTemp: {t}  | LastAVG: {temp}")
    print("\n")

    while True:
        print(f"Buffer: {tc.buffer}  |  LastTemp: {t}  | LastAVG: {temp}")
        t = tc.readTC()
        temp = tc.readTempC_average()
        time.sleep(0.5)
except KeyboardInterrupt:
    input("Terminato")