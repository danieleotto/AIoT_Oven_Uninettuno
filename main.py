import json
from termocoppia import Termocoppia
from sqlite3db import SQLite3DB
from ssrelay import SolidStateRelay
from consoleMenu import TextMenu, ANSI
from processi import Essicatura, Ricottura, SaldaturaSMD
#from dht22 import DHT22
#from PZEM004Tlib import PZEM004T
#from PZEM004TModbuslib import PZEM004TModbus #alternativa da controllare


class Context:
    def __init__(self, thermocouple, samplinginterval, database, ssr_resistance, ssr_ovenfan, dht22=None, pzem=None):
        self.tc = thermocouple
        self.sampling_interval = samplinginterval
        self.sq = database
        self.ssr_res = ssr_resistance
        self.ssr_fan = ssr_ovenfan
        self.dht22 = dht22
        self.pzem = pzem

with open("config.json") as configFile:
    configData = json.load(configFile)

TC_SCK_PIN = configData["TC_PIN_SCK"]
TC_CS_PIN = configData["TC_PIN_CS"]
TC_DO_PIN = configData["TC_PIN_DO"]
RES_SSR_PIN = configData["RES_SSR_PIN"]
FAN_SSR_PIN = configData["FAN_SSR_PIN"]
#DHT22_PIN = configData["DHT22_PIN"]
sample_size = configData["avg_sample_size"]
sampling_interval = configData["sample_interval"]

tc = Termocoppia(TC_SCK_PIN, TC_CS_PIN, TC_DO_PIN,sample_size)
sq = SQLite3DB(configData["db_filename"])
#dht22 = DHT22(DHT22_PIN)
#pzem = PZEM004T(configData["PZEM_port"], configData["PZEM_timeout"])
#pzem2 = PZEM004TModbus() #aternativa da controllare
ssr_res = SolidStateRelay(RES_SSR_PIN)
ssr_fan = SolidStateRelay(FAN_SSR_PIN)

ctx = Context(tc, sampling_interval, sq, ssr_res, ssr_fan)

eProc = Essicatura(ctx)
rProc = Ricottura(ctx)
sProc = SaldaturaSMD(ctx)

menu_principale = TextMenu("             --- MENU PRINCIPALE ---", color_title=ANSI.GREEN, color_option=ANSI.CYAN)
menu_principale.add_option("1", "Essicartura", eProc.textMenu)
menu_principale.add_option("2", "Ricottura", rProc.textMenu)
menu_principale.add_option("3", "Saldatura SMD", sProc.textMenu)

menu_principale.run()

sq.logProcesses()
