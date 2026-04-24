import adafruit_dht

class DHT22():
    def __init__(self, pin_dht22):
        self.sensor = adafruit_dht.DHT22(pin_dht22)
        self.temp = None
        self.hum = None

    def getTemp(self):
        self.temp = self.sensor.temperature
        return self.temp

    def getHum(self):
        self.hum = self.sensor.humidity
        return self.hum




