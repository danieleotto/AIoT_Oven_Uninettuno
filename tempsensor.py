import customlib.dht as dht

class TempSensor:
    def __init__(self, pin, sensorType=22):
        self.pin = pin
        self.sensor = sensorType
        self.sensor = dht.DHT(self.pin, sensorType)
    
    def _read(self):
        result = self.sensor.read()
        if result.is_valid():
            return result.temperature, result.humidity
        return -200, -1
    
    def getTemperature(self):
        temp, _ = self._read()
        return temp
    
    def getHumidity(self):
        _, hum = self._read()
        return hum