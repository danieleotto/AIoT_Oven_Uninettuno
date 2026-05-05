from MAX6675lib import MAX6675
import json, time

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
    while True:
        print(f"Buffer: {tc.buffer}  |  LastTemp: {t}  | LastAVG: {temp}")
        t = tc.readTC()
        temp = tc.readTempC_average()
        time.sleep(1)
except KeyboardInterrupt:
    input("Terminato")