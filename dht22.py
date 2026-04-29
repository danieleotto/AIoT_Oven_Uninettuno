import dht

class DHT22:
    def __init__(self, pin):
        self.pin = pin
        self.sensor = dht.DHT(self.pin)
    
    def _read(self):
        result = self.sensor.read()
        if result.is_valid():
            return result.temperature, result.humidity
        return None, None
    
    def getTemperature(self):
        temp, _ = self._read()
        return temp
    
    def getHumidity(self):
        _, hum = self._read()
        return hum