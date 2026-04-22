import wiringpi as wp
from wiringpi import GPIO
import time

class Thermocouple6675(object):
    def __init__(self, _sck, _cs, _do):
        self.sck = _sck
        self.cs = _cs
        self.do = _do

        wp.wiringPiSetup()

        wp.pinMode(self.sck, wp.OUTPUT)
        wp.pinMode(self.cs, wp.OUTPUT)
        wp.pinMode(self.do, wp.INPUT)

        wp.digitalWrite(self.cs, 1)
        wp.digitalWrite(self.sck, 0)


    def readTempC(self):
        wp.digitalWrite(self.cs, 0)
        time.sleep(0.001)

        value = 0

        for i in range (16):
            wp.digitalWrite(self.sck, 1)
            time.sleep(0.001)

            value <<= 1
            if wp.digitalRead(self.do):
                value |= 1

            wp.digitalWrite(self.sck, 0)
            time.sleep(0.001)

        wp.digitalWrite(self.cs, 1)

        if value & 0x04:
            return None

        temp_c = (value >> 3) * 0.25
        return temp_c

    def readTempF(self):
        temp_f = (self.readTempC() * (9/5)) + 32
        return temp_f
