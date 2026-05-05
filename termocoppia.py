import wiringpi as wp
from wiringpi import GPIO
import time
from collections import deque

class Termocoppia(object):
    def __init__(self, pin_sck, pin_cs, pin_do,sample_size):
        self.PIN_SCK = pin_sck
        self.PIN_CS = pin_cs
        self.PIN_DO = pin_do
        self.sample_size = sample_size
        self.buffer = deque(maxlen=self.sample_size)

        wp.wiringPiSetup()
        wp.pinMode(self.PIN_SCK, GPIO.OUTPUT)
        wp.pinMode(self.PIN_CS, GPIO.OUTPUT)
        wp.pinMode(self.PIN_DO, GPIO.INPUT)
        wp.digitalWrite(self.PIN_SCK, 0)
        wp.digitalWrite(self.PIN_CS, 1)


    def readTC(self):
        wp.digitalWrite(self.PIN_CS, 0)
        time.sleep(0.001)

        value = 0

        for i in range(16):
            wp.digitalWrite(self.PIN_SCK, 1)
            time.sleep(0.00001)
            value <<= 1
            if wp.digitalRead(self.PIN_DO):
                value |= 1
            wp.digitalWrite(self.PIN_SCK, 0)
            time.sleep(0.00001)

        wp.digitalWrite(self.PIN_CS, 1)

        if value & 0x04:
            return None

        temp_c = round((value >> 3) * 0.25,1)
        return temp_c

    
    def readTempC_average(self):
        temp = self.readTC()
        if temp is not None:
            if len(self.buffer) == 10:
                if -15 <  self.getAverage() - temp < 15:
                    self.buffer.append(temp)
            else:
                if 0 < temp < 300:
                    self.buffer.append(temp)
        else:
            print(f"\rTermocoppia non collegata.")
        if not self.buffer:
            return None
        else:
            avg = self.getAverage()
        return avg

    def getAverage(self):
        if not self.buffer:
            return None
        else:
            return sum(self.buffer) / len(self.buffer)
