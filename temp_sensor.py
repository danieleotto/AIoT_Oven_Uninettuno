import customlib.dht as dht

class TempSensor:
    def __init__(self, pin:int, sensor_type:int = 22) -> None:
        self.pin = pin
        self.sensor_type = sensor_type
        self.sensor = dht.DHT(self.pin, self.sensor_type)
    
    def _read(self) -> float:
        result = self.sensor.read()
        if result.is_valid():
            return result.temperature, result.humidity
        return -200.0, -1.0
    
    def get_temperature(self) -> float:
        temp, _ = self._read()
        return temp
    
    def get_humidity(self) -> float:
        _, hum = self._read()
        return hum