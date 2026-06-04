import wiringpi as wp
import time, sys
from wiringpi import GPIO
from collections import deque
from customlib.functions import ask_continue
from customlib.exceptions import ErroreSonda, ErroreMaxTemp


def debug_buffer_print(buffer:deque) -> str:
    string = "("
    string += ", ".join(str(e) for e in buffer)
    string += ")"
    return string

def debug_list_print(readings:list[float]) -> str:
    string = "("
    string += ", ".join(str(r) for r in readings)
    string += ")"
    return string




class Termocoppia:
    def __init__(self, pin_sck:int, pin_cs:int, pin_do:int, sample_size:int, tc_max_temp:float=235) -> None:
        self.PIN_SCK = pin_sck
        self.PIN_CS = pin_cs
        self.PIN_DO = pin_do
        self.sample_size = sample_size
        self.tc_max_temp = tc_max_temp
        self.buffer = deque(maxlen=self.sample_size)

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

        # temp_c = round((value >> 3) * 0.25,1)
        temp_c = (value >> 3) * 0.25
        
        if temp_c > self.tc_max_temp:
            raise ErroreMaxTemp
        else:
            return temp_c
        
        
    def _get_average(self) -> float | None:
        if not self.buffer:
            return None
        else:
            return sum(self.buffer) / len(self.buffer)
    
    
    def _inizializza(self, sampling_interval:float, debug:bool = False) -> float | None:
        self.buffer.clear()
        print(f"Inizializzazione sonda.\nEseguo {self.sample_size} letture con intervallo {sampling_interval:.1f} s.\n\n")
        if debug:
            print(f"{debug_buffer_print(self.buffer)}")
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
                print(f"Buffer: {debug_buffer_print(self.buffer)}  | LastAVG: {t}")
            if counter > self.sample_size * tentativi:
                tentativi += 1
                if not ask_continue("Termocoppia non rilevata. Riprovare? [Y/n]: "):
                    return None
                sys.stdout.write("\033[F\033[K")
        print("\n")
        return t


    def controllo_sonda(self, sampling_interval:float, debug:bool = False) -> float:
        result = self._inizializza(sampling_interval, debug)
        if result is None:
            raise ErroreSonda
        else:
            return float(result)
        
        
    def read_temp_raw(self) -> float | None:
        return self._read_tc()

 
    def read_temp_average(self) -> float | None:
        temp = self._read_tc()
        if temp is not None:
            if len(self.buffer) == self.sample_size:
                avg = self._get_average()
                if -15 < temp - avg < 15:
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


    def read_temp_safe(self) -> float:
        temp = self.read_temp_average()
        if temp is None:
            raise ErroreSonda
        else:
            return temp
        
    
    def read_temp_filtered(self, samples:int=9, delay:float=0.005, debug:bool=False) -> float:
        readings:list[float] = []
        while len(readings) <= samples:
            t = self._read_tc()
            if t is not None:
                readings.append(t)
            time.sleep(delay)
        readings.sort()
        filtered_readings = readings[1:-1]
        avg_temp = sum(filtered_readings) / len(filtered_readings)
        if debug:
            print(f"Readings: {readings} | Filtered: {filtered_readings} | AVERAGE: {avg_temp:.1f}")
        return avg_temp
    
    
    def read_temp_filtered_median(self, samples:int=9, delay:float=0.005, max_deviation:float=3.0, debug:bool=False):
        readings:list[float] = []
        while len(readings) <= samples:
            t = self._read_tc()
            if t is not None:
                readings.append(t)
            time.sleep(delay)
        
        #Calcolo mediana
        readings_sorted = sorted(readings)
        mid = len(readings_sorted) // 2
        if len(readings_sorted) % 2 == 1:
            median = readings_sorted[mid]
        else:
            median = (readings_sorted[mid-1] + readings_sorted[mid+1]) / 2
            
        #Elimino outlier
        filtered_readings = [r for r in readings if abs(r - median) <= max_deviation]
        
        #Fallback alla mediana se sono tutti troppo variabili
        if not filtered_readings:
            if debug:
                print(f"Readings: {readings} | No Filtered | MEDIAN: {median:.1f}")
            return median
        
        avg_temp = sum(filtered_readings) / len(filtered_readings)
        if debug:
            print(f"Readings: {readings} | Filtered: {filtered_readings} | AVERAGE: {avg_temp:.1f}")
        
        return avg_temp