import time
from ss_relay import SolidStateRelay

class PID:
    def __init__(self, kp:float, ki:float, kd:float, temp_target:float) -> None:
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.temp_target = temp_target
        self.min_output:float = 0.0
        self.max_output:float = 1.0
        self.integrale:float = 0.0
        self.last_error = None
        self.last_time = None
        
    
    def calcola_output(self, temp_attuale:float) -> float:
        """Calcola l'output di potenza con PID in base al valore misurato"""
        t:float = time.time()
        errore:float = self.temp_target - temp_attuale
        
        if self.last_time is None:
            delta_time:float = 0.0
        else:
            delta_time = t - self.last_time
        
        #Parte Proporzionale    
        p:float = self.kp * errore
        
        #Parte Integrale
        if delta_time > 0:
            self.integrale += errore * delta_time
        i:float = self.ki * self.integrale
        
        #Parte Derivata
        if self.last_error is None or delta_time == 0:
            d:float = 0
        else:
            d = self.kd * (errore - self.last_error) / delta_time
            
        output:float = p + i + d
        output = max(self.min_output, min(self.max_output, output))
        
        self.last_error = errore
        self.last_time = t
        
        return output
    


class PWM:
    def __init__(self, ssr:SolidStateRelay, frequenza:float = 1.0):
        self.ssr = ssr
        self.periodo = 1 / frequenza
        self.duty_cycle = 0.0 #deve essere tra 0 e 1
        self.last_time = time.time()
        
    
    def pid_output(self, power:float):
        self.duty_cycle = max(0.0, min(1.0, power))
        adesso = time.time()
        t = (adesso - self.last_time) % self.periodo
        tempo_accensione = self.periodo * self.duty_cycle
        
        if t < tempo_accensione:
            self.ssr.turn_on()
        else:
            self.ssr.turn_off()