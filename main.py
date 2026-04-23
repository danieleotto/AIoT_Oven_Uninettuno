import sys, time, json
from datetime import datetime
from max6675lib import MAX6675, MovingAverage
from logger import FileLogger
from sqlite3db import SQLite3DB
from ssrelay import SSR

with open("config.json") as configFile:
    configData = json.load(configFile)

TC_PIN_SCK = configData["TC_PIN_SCK"]
TC_PIN_CS = configData["TC_PIN_CS"]
TC_PIN_DO = configData["TC_PIN_DO"]
RES_SSR_PIN = configData["RES_SSR_PIN"]
FAN_SSR_PIN = configData["FAN_SSR_PIN"]
interval = configData["sample_interval"]

tc = MAX6675(TC_PIN_SCK, TC_PIN_CS, TC_PIN_DO)
ma = MovingAverage(configData["avg_sample_size"])
lg = FileLogger()
sq = SQLite3DB(configData["db_filename"])
ssr_res = SSR(RES_SSR_PIN)
ssr_fan = SSR(FAN_SSR_PIN)

target = float(input("Inserire temperatura target: "))
n_camp = 1

try:
    print("Press CTRL+C to exit")
    start_time = time.time()
    while True:
        temp = tc.readTempC()
        if temp is not None:
            ma.add(temp)
        else:
            sys.stdout.write(f"\rTermocoppia non collegata.")
        time.sleep(interval)

        elapsed_time = time.time() - start_time
        avg = ma.average()

        if avg < target:
            ssr_res.HIGH()
        else:
            ssr_res.LOW()

        sys.stdout.write(f"\rTemperatura media ultimi {ma.size} campioni: {avg:.2f} °C | Tempo: {elapsed_time:.2f} s | SSR1: {ssr_res.getState()} | SSR2: {ssr_fan.getState()} |Numero campione: {n_camp}")
        lg.log(f"{avg:.2f},{elapsed_time:.2f},{ssr_res.getState()},{ssr_fan.getState()}{n_camp}\n")
        sq.add(datetime.now().isoformat(),elapsed_time,avg,ssr_res.isOn,ssr_fan.isOn)
        n_camp += 1


except KeyboardInterrupt:
    print("\nProgram terminated.")
    ssr_res.LOW()
    ssr_fan.LOW()
    rows = sq.readAll()
    for row in rows:
        print(row)