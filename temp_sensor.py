import customlib.dht as dht

class TempSensor:
    def __init__(self, pin:int, sensor_type:int = 22) -> None:
        self.pin = pin
        self.sensor_type = sensor_type
        self.sensor = dht.DHT(self.pin, self.sensor_type)
        self.last_safe_temp:float | None = None
        self.last_safe_hum:float | None = None
        self.temp_counter:int = 0
        self.hum_counter:int = 0
    
    def _read(self) -> tuple[float | None, float | None]:
        result = self.sensor.read()
        if result.is_valid():
            return result.temperature, result.humidity
        else:
            return None, None
    
    def get_temperature(self) -> float:
        temp, _ = self._read()
        return temp
    
    def get_humidity(self) -> float:
        _, hum = self._read()
        return hum
    
    def get_safe_temp(self) -> float:
        t = self.get_temperature()
        if t is not None:
            self.last_safe_temp = t
            return t
        else:
            if self.last_safe_temp is not None and self.temp_counter < 10:
                self.temp_counter += 1
                return self.last_safe_temp
            else:
                self.temp_counter = 0
                return -200.0
            
    def get_safe_hum(self) -> float:
        h = self.get_humidity()
        if h is not None:
            self.last_safe_hum = h
            return h
        else:
            if self.last_safe_hum is not None and self.hum_counter < 10:
                self.hum_counter += 1
                return self.last_safe_hum
            else:
                self.hum_counter = 0
                return -1.0              