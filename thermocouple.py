import wiringpi as wp
import time, sys, statistics
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
        self.last_good_sample:float = -100.0

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
        self.last_good_sample = -100.0
        print(f"Inizializzazione sonda.\nEseguo {self.sample_size} letture con intervallo {sampling_interval:.1f} s.\n\n")
        if debug:
            print(f"{debug_buffer_print(self.buffer)}")
        t = None # Per evitare che venga ritornato prima di esistere
        counter = 0
        tentativi = 1
        while len(self.buffer) != self.sample_size:
            # t = self.read_temp_average()
            t = self.read_temp_filtered()
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
        # temp = self.read_temp_average()
        temp = self.read_temp_filtered()
        if temp is None:
            raise ErroreSonda
        else:
            return temp
        
    
    def read_temp_filtered(self, 
                           max_deviation:float=3.0, 
                           min_valid:float=10.0, 
                           max_valid:float=300.0, 
                           tentativi:int = 5, 
                           debug:bool=False) -> float:
        
        for _ in range(tentativi):
            t = self._read_tc()
            
            if t is None:
                continue
            
            if not (min_valid <= t <= max_valid):
                continue
            
            t = float(t)
            self.buffer.append(t)
            self.last_good_sample = t
            break
        else:
            if debug:
                print(f"Lettura non valida dopo {tentativi} tentativi: Ultimo dato valido: {self.last_good_sample:.1f}")
            return self.last_good_sample
        
        # t = self._read_tc()
        # if t is None:
        #     counter = 0
        #     while t is None:
        #         t = self._read_tc()
        #         counter += 1
        #         if counter > 10:
        #             raise ErroreSonda
        # self.buffer.append(t)
        
        # Se troppi pochi dati ritorna la media semplice
        if len(self.buffer) < 3:
            if debug:
                print(f"Meno di tre campioni: media semplice temperatura: {t:.1f}")
            return sum(self.buffer) / len(self.buffer)
        
        # Ordina i valori e rimuove il min e il max
        sorted_val = sorted(self.buffer)
        trimmed_val = sorted_val[1:-1]
        
        # Calcolo mediana e filtro i valori oltre la max_deviation dalla mediana
        median = statistics.median(trimmed_val)
        filtered = [v for v in trimmed_val if abs(v - median) <= max_deviation]
        
        # Se tutti i valori sono da scartare allora fallback sulla mediana, altrimenti media del restante
        if not filtered:
            if debug:
                print(f"Buffer: {debug_buffer_print(self.buffer)}  | MEDIAN: {median:.1f}")
            return median
        
        avg_temp = sum(filtered) / len(filtered)
        if debug:
            print(f"Buffer: {debug_buffer_print(self.buffer)}  | AVERAGE: {median:.1f}")
        return avg_temp