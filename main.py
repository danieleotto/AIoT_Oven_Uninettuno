import json
from thermocouple import Termocoppia
from sqlite_db import SQLiteDB
from ss_relay import SolidStateRelay
from console_menu import TextMenu, ANSI
from processi import Essicatura, Ricottura, SaldaturaSMD
from temp_sensor import TempSensor
#from dht22 import DHT22
#from PZEM004Tlib import PZEM004T
#from PZEM004TModbuslib import PZEM004TModbus #alternativa da controllare

class Context:
    def __init__(
        self, 
        thermocouple:Termocoppia,
        sampling_interval:float,
        database:SQLiteDB,
        ssr_resistance:SolidStateRelay,
        ssr_fan:SolidStateRelay,
        dht22:TempSensor = None,
        pzem = None
    ) -> None:
        #TODO pzem sensor type
        self.tc = thermocouple
        self.sampling_interval = sampling_interval
        self.sq = database
        self.ssr_res = ssr_resistance
        self.ssr_fan = ssr_fan
        self.dht22 = dht22
        self.pzem = pzem

with open("config.json") as config_file:
    config_data = json.load(config_file)

TC_SCK_PIN:int = config_data["TC_PIN_SCK"]
TC_CS_PIN:int = config_data["TC_PIN_CS"]
TC_DO_PIN:int = config_data["TC_PIN_DO"]
RES_SSR_PIN:int = config_data["RES_SSR_PIN"]
FAN_SSR_PIN:int = config_data["FAN_SSR_PIN"]
#DHT22_PIN:int = config_data["DHT22_PIN"]
sample_size:int = config_data["avg_sample_size"]
sampling_interval:float = config_data["sample_interval"]

tc:Termocoppia = Termocoppia(TC_SCK_PIN, TC_CS_PIN, TC_DO_PIN,sample_size)
sq:SQLiteDB = SQLiteDB(config_data["db_filename"])
#dht22:TempSensor = TempSensor(DHT22_PIN)
#pzem:PZEM004T = PZEM004T(config_data["PZEM_port"], config_data["PZEM_timeout"])
#pzem2:PZEM004TModbus = PZEM004TModbus() #aternativa da controllare
ssr_res:SolidStateRelay = SolidStateRelay(RES_SSR_PIN)
ssr_fan:SolidStateRelay = SolidStateRelay(FAN_SSR_PIN)

ctx:Context = Context(tc, sampling_interval, sq, ssr_res, ssr_fan)

e_proc:Essicatura = Essicatura(ctx)
r_proc:Ricottura = Ricottura(ctx)
s_proc:SaldaturaSMD = SaldaturaSMD(ctx)

menu_principale:TextMenu = TextMenu("             --- MENU PRINCIPALE ---", color_title=ANSI.GREEN, color_option=ANSI.CYAN)
menu_principale.add_option("1", "Essicartura", e_proc.process_menu)
menu_principale.add_option("2", "Ricottura", r_proc.process_menu)
menu_principale.add_option("3", "Saldatura SMD", s_proc.process_menu)

if __name__ == '__main__':
    menu_principale.run()
    sq.log_processes()