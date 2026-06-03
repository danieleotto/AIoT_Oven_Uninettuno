import time
from ss_relay import SolidStateRelay

class PID:
    def __init__(self, kp:float | None = None, ki:float | None = None, kd:float | None = None, temp_target:float | None = None) -> None:
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.temp_target = temp_target
        self.min_output:float = 0.0
        self.max_output:float = 1.0
        self.integrale:float = 0.0
        self.last_error = None
        self.last_time = None
        
    
    def set_pid(self, kp:float, ki:float, kd:float) -> None:
        self.kp = kp
        self.ki = ki
        self.kd = kd


    def set_pid_target(self, temp_target:float) -> None:
        self.temp_target = temp_target


    def calcola_output(self, temp_attuale:float) -> float:
        """Calcola l'output di potenza con PID in base al valore misurato"""
        t:float = time.time()
        errore:float = self.temp_target - temp_attuale
        
        if errore >= 0: #riscaldamento in corso
            if self.last_time is None:
                delta_time:float = 0.0
            else:
                delta_time = t - self.last_time
            
            #Parte Proporzionale    
            p:float = self.kp * errore

            #Parte Derivata
            if self.last_error is None or delta_time == 0:
                d:float = 0
            else:
                d = self.kd * (errore - self.last_error) / delta_time

            #Parte Integrale con anti-windup
            if delta_time > 0:
                #controlliamo quale sarebbe il valore di output al momento
                i_temporaneo = self.ki * (self.integrale + errore * delta_time)
                output_temporaneo = p + i_temporaneo + d
                
                #anti-windup: aumentiamo l'integrale solo se non già 1
                if self.min_output < output_temporaneo < self.max_output:
                    self.integrale += errore * delta_time
                else:
                    pass
                
            i:float = self.ki * self.integrale
            
            output:float = p + i + d
            output = max(self.min_output, min(self.max_output, output))
            
            self.last_error = errore
            self.last_time = t
        else: #raffreddamento, default power a 0
            output = 0.0
        
        return output
            
    
    def calcola_output_limitato_up(self, temp_attuale:float, temp_rate:float, target_temp_rate:float | None) -> float:
        if target_temp_rate is not None and temp_rate > target_temp_rate: #salita temperatura troppo rapida
            #calcoliamo l'output in base a quanto stiamo sforando il target_temp_rate con fattore di scala
            e:float = (temp_rate - target_temp_rate) / target_temp_rate
            K:float = 0.5
            output_corretto:float = self.calcola_output(temp_attuale) * (1 / (1 + K * e))
            output_corretto = max(0.0, min(1.0, output_corretto))
            return output_corretto
        else: #riscaldamento senza limiti oppure temp_rate sotto il target
            return self.calcola_output(temp_attuale)
            

    def calcola_output_limitato_down(self, temp_attuale:float, temp_rate:float, target_temp_rate:float | None) -> float:
        if target_temp_rate is None: #nessun limite su velocità raffreddamento
            return 0.0

        if target_temp_rate > 0: #inserito valore positivo per raffreddamento, lo invertiamo
            target_temp_rate = target_temp_rate * -1
            
        if temp_rate < target_temp_rate: #raffreddamento troppo veloce
            #calcoliamo output in base a sforamento con fattore scala
            e:float = (target_temp_rate - temp_rate) / abs(target_temp_rate)
            K:float = 0.5
            output_corretto:float = self.calcola_output(temp_attuale) + K * e
            output_corretto = max(0.0, min(1.0, output_corretto))
            return output_corretto
        else: #raffreddamento più lento
            return 0.0 #al momento lasciamo resistenze spente senza TODO lavorare sulla ventola
        

class PWM:
    def __init__(self, ssr:SolidStateRelay, frequenza:float = 1.0) -> None:
        self.ssr = ssr
        self.periodo = 1 / frequenza
        self.duty_cycle = 0.0 #deve essere tra 0 e 1
        self.start_time = time.time()
        
    
    def update(self, power:float) -> None:
        self.duty_cycle = max(0.0, min(1.0, power))
        adesso = time.time()
        t = (adesso - self.start_time) % self.periodo
        tempo_accensione = self.periodo * self.duty_cycle

        if t < tempo_accensione:
            self.ssr.turn_on()
        else:
            self.ssr.turn_off()