import wiringpi as wp
from wiringpi import GPIO
import time

class MAX6675(object):
    def __init__(self, PIN_SCK, PIN_CS, PIN_DO):
        self.PIN_SCK = PIN_SCK
        self.PIN_CS = PIN_CS
        self.PIN_DO = PIN_DO

        wp.wiringPiSetup()

        wp.pinMode(self.PIN_SCK, GPIO.OUTPUT)
        wp.pinMode(self.PIN_CS, GPIO.OUTPUT)
        wp.pinMode(self.PIN_DO, GPIO.INPUT)

        wp.digitalWrite(self.PIN_SCK, 0)
        wp.digitalWrite(self.PIN_CS, 1)


    def readTempC(self):
        wp.digitalWrite(self.PIN_CS, 0)
        time.sleep(0.001)

        value = 0

        for i in range(16):
            wp.digitalWrite(self.PIN_SCK, 1)
            time.sleep(0.001)
            value <<= 1
            if wp.digitalRead(self.PIN_DO):
                value |= 1
            wp.digitalWrite(self.PIN_SCK, 0)
            time.sleep(0.001)

        wp.digitalWrite(self.PIN_CS, 1)

        if value & 0x04:
            return None

        temp_c = (value >> 3) * 0.25
        return temp_c


    def readTempF(self):
        temp_f = (self.readTempC() * (9/5)) + 32
        return temp_f