from termocoppia import Termocoppia
import json, time, sys

with open("config.json") as configFile:
    configData = json.load(configFile)
    
TC_SCK = configData["TC_PIN_SCK"]
TC_CS = configData["TC_PIN_CS"]
TC_DO = configData["TC_PIN_DO"]
interval = configData["sample_interval"]
sample_size = configData["avg_sample_size"]

tc = Termocoppia(TC_SCK,TC_CS,TC_DO, sample_size)

startTime = lastTime = time.time()
temp = t = 0
sampling = 0.3
try:
    tc.inizializza(sampling_interval=sampling, debug=True)
    print("\n")

    while True:
        print(f"Buffer: {tc.buffer}  |  LastTemp: {t}  | LastAVG: {temp}")
        t = tc.readTC()
        temp = tc.readTempC_average()
        time.sleep(sampling)
except KeyboardInterrupt:
    input("Terminato")