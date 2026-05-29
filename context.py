from thermocouple import Termocoppia
from sqlite_db import SQLiteDB
from ss_relay import SolidStateRelay
from temp_sensor import TempSensor
from customlib.pzem004t_modbus_lib import PZEM004TModbus
from customlib.sgp30 import SGP30


class Context:
    def __init__(
        self, 
        thermocouple:Termocoppia,
        sanpling_interval:float,
        database:SQLiteDB,
        ssr_resistance:SolidStateRelay,
        ssr_ovenfan:SolidStateRelay,
        dht22:TempSensor,
        pzem:PZEM004TModbus,
        sgp:SGP30,
        pid_values:dict[str, float]
    ) -> None:
        self.tc = thermocouple
        self.sampling_interval = sanpling_interval
        self.sq = database
        self.ssr_res = ssr_resistance
        self.ssr_fan = ssr_ovenfan
        self.dht22 = dht22
        self.pzem = pzem
        self.sgp = sgp
        self.pid_values = pid_values