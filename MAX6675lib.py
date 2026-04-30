import wiringpi as wp
from wiringpi import GPIO
import time
from collections import deque

class MAX6675(object):
    def __init__(self, pin_sck, pin_cs, pin_do,sample_size=1,interval=0.2):
        self.PIN_SCK = pin_sck
        self.PIN_CS = pin_cs
        self.PIN_DO = pin_do
        self.sample_size = sample_size
        self.interval = interval
        self.buffer = deque(maxlen=self.sample_size)

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
            time.sleep(0.00001)
            value <<= 1
            if wp.digitalRead(self.PIN_DO):
                value |= 1
            wp.digitalWrite(self.PIN_SCK, 0)
            time.sleep(0.00001)

        wp.digitalWrite(self.PIN_CS, 1)

        if value & 0x04:
            return None

        temp_c = (value >> 3) * 0.25
        return temp_c
    
    def readTempC_average(self):
        temp = self.readTempC()
        if temp is not None:
            self.addAvg(temp)
        else:
            print(f"\rTermocoppia non collegata.")
        avg = self.getAverage()
        return avg

    def readTempF(self):
        temp_f = (self.readTempC() * (9/5)) + 32
        return temp_f

    def readTempF_average(self):
        avg_f = (self.readTempC_average() * (9/5)) + 32
        return avg_f


# class MovingAverage:
#     def __init__(self, sample_size):
        # self.size = sample_size
        # self.buffer = deque(maxlen=self.size)

    def addAvg(self, value):
        self.buffer.append(value)

    def getAverage(self):
        if not self.buffer:
            return None
        return sum(self.buffer) / len(self.buffer)