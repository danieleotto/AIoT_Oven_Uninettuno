import sys, time, json
from datetime import datetime
from MAX6675lib import MAX6675, MovingAverage
from logger import FileLogger
from sqlite3db import SQLite3DB
from ssrelay import SSR
from consoleMenu import TextMenu, ANSI
from processi import Essicatura, Ricottura, SaldaturaSMD
#from dht22 import DHT22
#from PZEM004Tlib import PZEM004T
#from PZEM004TModbuslib import PZEM004TModbus #alternativa da controllare


# def essicatura():
#     target = float(input("Inserire temperatura target: "))
#     process = 1
#     try:
#         print("Press CTRL+C to exit")
#         start_time = time.time()
#         while True:
#             temp = tc.readTempC()
#             if temp is not None:
#                 ma.add(temp)
#             else:
#                 sys.stdout.write(f"\rTermocoppia non collegata.")
#             time.sleep(interval)

#             elapsed_time = time.time() - start_time
#             avg = ma.average()

#             if avg < target:
#                 ssr_res.HIGH()
#             else:
#                 ssr_res.LOW()

#             #sysTemp = dht22.getTemperature()
#             sysTemp = 22.0
#             idproc = sq.getLastId("listaprocessi")
#             sq.addSample(idproc, avg, target, elapsed_time, ssr_res.getState(), ssr_fan.getState(), sysTemp)
#             idsample = sq.getLastId("campioni")
#             lg.log(f"{idproc},{process},{idsample},{target:.2f},{avg:.2f},{elapsed_time:.2f},{ssr_res.getState()},{ssr_fan.getState()}{sysTemp:.2f}\n")
#             sys.stdout.write(f"\rAvg temp lasr  {ma.size} samples: {avg:.2f} °C | Time: {elapsed_time:.2f} s | SSR_R: {ssr_res.getState()} | SSR_F: {ssr_fan.getState()} Sample#: {idsample}")

#     except KeyboardInterrupt:
#         print("\nProgram terminated.")
#         ssr_res.LOW()
#         ssr_fan.LOW()
#         rows = sq.readProcesses()
#         rows2 = sq.readSamples()
#         for row in rows:
#             print(row)
#         for row in rows2:
#             print(row)

class Context:
    def __init__(self, tc, lg, sq, ssr_res, ssr_fan, dht22=None, pzem=None):
        self.tc = tc
        self.lg = lg
        self.sq = sq
        self.ssr_res = ssr_res
        self.ssr_fan = ssr_fan
        self.dht22 = dht22
        self.pzem = pzem

with open("config.json") as configFile:
    configData = json.load(configFile)

TC_PIN_SCK = configData["TC_PIN_SCK"]
TC_PIN_CS = configData["TC_PIN_CS"]
TC_PIN_DO = configData["TC_PIN_DO"]
RES_SSR_PIN = configData["RES_SSR_PIN"]
FAN_SSR_PIN = configData["FAN_SSR_PIN"]
#DHT22_PIN = configData["DHT22_PIN"]
interval = configData["sample_interval"]
sample_size = configData["avg_sample_size"]

tc = MAX6675(TC_PIN_SCK, TC_PIN_CS, TC_PIN_DO,sample_size,interval)
#ma = MovingAverage(configData["avg_sample_size"])
lg = FileLogger()
sq = SQLite3DB(configData["db_filename"])
#dht22 = DHT22(DHT22_PIN)
#pzem = PZEM004T(configData["PZEM_port"], configData["PZEM_timeout"])
#pzem2 = PZEM004TModbus() #aternativa da controllare
ssr_res = SSR(RES_SSR_PIN)
ssr_fan = SSR(FAN_SSR_PIN)

ctx = Context(tc, lg, sq, ssr_res, ssr_fan)

eProc = Essicatura(ctx)
rProc = Ricottura()
sProc = SaldaturaSMD()

menu_principale = TextMenu("Menu Principale - Scelta Processo", color_title=ANSI.GREEN, color_option=ANSI.CYAN)
menu_principale.add_option("1", "Essicatura", eProc.textMenu)
menu_principale.add_option("2", "Ricottura", rProc.textMenu)
menu_principale.add_option("3", "Saldatura SMD", sProc.textMenu)

menu_principale.run()





