import json
from MAX6675lib import MAX6675
from logger import FileLogger
from sqlite3db import SQLite3DB
from ssrelay import SSR
from consoleMenu import TextMenu, ANSI
from processi import Essicatura, Ricottura, SaldaturaSMD
#from dht22 import DHT22
#from PZEM004Tlib import PZEM004T
#from PZEM004TModbuslib import PZEM004TModbus #alternativa da controllare


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
lg = FileLogger()
sq = SQLite3DB(configData["db_filename"])
#dht22 = DHT22(DHT22_PIN)
#pzem = PZEM004T(configData["PZEM_port"], configData["PZEM_timeout"])
#pzem2 = PZEM004TModbus() #aternativa da controllare
ssr_res = SSR(RES_SSR_PIN)
ssr_fan = SSR(FAN_SSR_PIN)

ctx = Context(tc, lg, sq, ssr_res, ssr_fan)

eProc = Essicatura(ctx)
rProc = Ricottura(ctx)
sProc = SaldaturaSMD(ctx)

menu_principale = TextMenu("Menu Principale - Scelta Processo", color_title=ANSI.GREEN, color_option=ANSI.CYAN)
menu_principale.add_option("1", "Essicatura", eProc.textMenu)
menu_principale.add_option("2", "Ricottura", rProc.textMenu)
menu_principale.add_option("3", "Saldatura SMD", sProc.textMenu)

menu_principale.run()





