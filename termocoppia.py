import wiringpi as wp
from wiringpi import GPIO
import time, sys
from collections import deque

class Termocoppia(object):
    def __init__(self, pin_sck, pin_cs, pin_do,sample_size):
        self.PIN_SCK = pin_sck
        self.PIN_CS = pin_cs
        self.PIN_DO = pin_do
        self.sample_size = sample_size
        self.buffer = deque(maxlen=self.sample_size)
        self.error_buffer = deque(maxlen=self.sample_size) #buffer per salvare le letture sbagliate

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
                avg = self.getAverage()
                if -15 < temp -avg < 15:
                    self.buffer.append(temp)
            else:
                if 0 < temp < 300:
                    self.buffer.append(temp)
            if not self.buffer:
                return None
            else:
                return self.getAverage()
        else:
            return None


    def safeReadTemp(self):
        temp = self.readTC()
        if temp is not None:
            #LETTURA
            pass
        else:
            print(f"\rTermocoppia non collegata.")


    def inizializza(self, sampling_interval, debug=False):
        self.buffer.clear()
        if debug:
            print(f"Buffer: {self.buffer}")
            time.sleep(1)
        print(f"Inizializzazione sonda.\nEseguo {self.sample_size} letture con intervallo {sampling_interval:.1f} s.\n")
        t = None #per evitare che venga ritornato prima di esistere
        while len(self.buffer) != self.sample_size:
            for i in range(1, self.sample_size + 1):
                t = self.readTempC_average()
                time.sleep(sampling_interval)
                sys.stdout.write("\033[F\033[K")
                text = "* " * i + "  " * (self.sample_size - i)
                print(f"{text} {i}/{self.sample_size}")
                if debug:
                    print(f"Buffer: {self.buffer}  |  LastTemp: {self.buffer[-1]}  | LastAVG: {t}")
        print("\n")
        return t

    def getAverage(self):
        if not self.buffer:
            return None
        else:
            return sum(self.buffer) / len(self.buffer)
