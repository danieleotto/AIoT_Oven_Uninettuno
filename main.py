import sys, time, json
from datetime import datetime
from MAX6675lib import MAX6675, MovingAverage
from logger import FileLogger
from sqlite3db import SQLite3DB
from ssrelay import SSR
#from dht22 import DHT22
#from PZEM004Tlib import PZEM004T
#from PZEM004TModbuslib import PZEM004TModbus #alternativa da controllare

with open("config.json") as configFile:
    configData = json.load(configFile)

TC_PIN_SCK = configData["TC_PIN_SCK"]
TC_PIN_CS = configData["TC_PIN_CS"]
TC_PIN_DO = configData["TC_PIN_DO"]
RES_SSR_PIN = configData["RES_SSR_PIN"]
FAN_SSR_PIN = configData["FAN_SSR_PIN"]
#DHT22_PIN = configData["DHT22_PIN"]
interval = configData["sample_interval"]

tc = MAX6675(TC_PIN_SCK, TC_PIN_CS, TC_PIN_DO)
ma = MovingAverage(configData["avg_sample_size"])
lg = FileLogger()
sq = SQLite3DB(configData["db_filename"])
#dht22 = DHT22(DHT22_PIN)
#pzem = PZEM004T(configData["PZEM_port"], configData["PZEM_timeout"])
#pzem2 = PZEM004TModbus() #aternativa da controllare
ssr_res = SSR(RES_SSR_PIN)
ssr_fan = SSR(FAN_SSR_PIN)

processList = {"1":"Essicatura", "2":"Ricottura", "3":"Saldatura SMD"}
process = ""
isOk = False
while not isOk:
    answer = input("Scegliere tipo di processo: \n1 - Essicatura\n2 - Ricottura\n3 - Saldatura SMD\n")
    if int(answer) >= 1 or int(answer) <= 3:
        process = processList[answer]
        isOk = True
    else:
        print("\nScelta non valida, riprovare.\n")

target = float(input("Inserire temperatura target: "))
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
sq.addProcess(timestamp, process)
idproc = sq.getLastId("listaprocessi")


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

        #sysTemp = dht22.getTemp()
        sysTemp = 22
        sys.stdout.write(f"\rTemperatura media ultimi {ma.size} campioni: {avg:.2f} °C | Tempo: {elapsed_time:.2f} s | SSR1: {ssr_res.getState()} | SSR2: {ssr_fan.getState()} |Numero campione: {n_camp}")
        #lg.log(f"{avg:.2f},{elapsed_time:.2f},{ssr_res.getState()},{ssr_fan.getState()}{n_camp}{sysTemp:.2f}\n")
        sq.addSample(idproc, avg, target, elapsed_time, ssr_res.getState(), ssr_fan.getState(), sysTemp)
        idsample = sq.getLastId("campioni")
        lg.log(f"{idproc},{process},{idsample},{target:.2f},{avg:.2f},{elapsed_time:.2f},{ssr_res.getState()},{ssr_fan.getState()}{sysTemp:.2f}\n")


except KeyboardInterrupt:
    print("\nProgram terminated.")
    ssr_res.LOW()
    ssr_fan.LOW()
    rows = sq.readProcesses()
    rows2 = sq.readSamples()
    for row in rows:
        print(row)
    for row in rows2:
        print(row)