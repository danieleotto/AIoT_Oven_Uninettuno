import wiringpi as wp
import time, sys
from wiringpi import GPIO
from collections import deque
from customlib.functions import ask_continue
from customlib.classes import ErroreSonda


class Termocoppia:
    def __init__(self, pin_sck:int, pin_cs:int, pin_do:int, sample_size:int) -> None:
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


    def _read_tc(self) -> float | None:
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

    
    def read_temp_average(self) -> float | None:
        temp = self._read_tc()
        if temp is not None:
            if len(self.buffer) == 10:
                avg = self._get_average()
                if -15 < temp -avg < 15:
                    self.buffer.append(temp)
            else:
                if 0 < temp < 300:
                    self.buffer.append(temp)
            if not self.buffer:
                return None
            else:
                return self._get_average()
        else:
            return None


    def safe_read_temp(self) -> float | None:
        #TODO logic
        temp = self._read_tc()
        if temp is not None:
            #LETTURA
            pass
        else:
            print(f"\rTermocoppia non collegata.")


    def _inizializza(self, sampling_interval:float, debug:bool = False) -> float | None:
        self.buffer.clear()
        print(f"Inizializzazione sonda.\nEseguo {self.sample_size} letture con intervallo {sampling_interval:.1f} s.\n\n")
        if debug:
            print(f"Buffer: {self.buffer}")
        t = None #per evitare che venga ritornato prima di esistere
        counter = 0
        tentativi = 1
        while len(self.buffer) != self.sample_size:
            t = self.read_temp_average()
            counter += 1
            time.sleep(sampling_interval)
            sys.stdout.write("\033[F\033[K")
            if debug:
                sys.stdout.write("\033[F\033[K")
            text = "* " * len(self.buffer) + "  " * (self.sample_size - len(self.buffer))
            print(f"{text} {len(self.buffer)}/{self.sample_size} - Tentativo n: {counter}")
            if debug:
                print(f"Buffer: {self.buffer}  |  LastTemp:   | LastAVG: {t}")
            if counter > self.sample_size * (tentativi):
                tentativi += 1
                if not ask_continue("Termocoppia non rilevata. Riprovare? [Y/n]: "):
                    return None
                sys.stdout.write("\033[F\033[K")
        print("\n")
        return t


    def _get_average(self) -> float | None:
        if not self.buffer:
            return None
        else:
            return sum(self.buffer) / len(self.buffer)
        
    
    def controllo_sonda(self, sampling_interval:float, debug:bool = False) -> float:
        result = self._inizializza(sampling_interval, debug)
        if result is None:
            raise ErroreSonda
        else:
            return result