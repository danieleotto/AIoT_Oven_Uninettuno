from thermocouple import Termocoppia
from sqlite_db import SQLiteDB
from ss_relay import SolidStateRelay
from temp_sensor import TempSensor


class Context:
    def __init__(
        self, 
        thermocouple:Termocoppia,
        sanpling_interval:float,
        database:SQLiteDB,
        ssr_resistance:SolidStateRelay,
        ssr_ovenfan:SolidStateRelay,
        dht22:TempSensor = None,
        pzem = None
    ) -> None:
        #TODO pzem sensor type
        self.tc = thermocouple
        self.sampling_interval = sanpling_interval
        self.sq = database
        self.ssr_res = ssr_resistance
        self.ssr_fan = ssr_ovenfan
        self.dht22 = dht22
        self.pzem = pzem