import time,sys,math
from customlib.functions import time_convert_str
from console_menu import ANSI
from customlib.exceptions import ErroreTemperatura, ErroreTimeout
from context import Context
from pid import PID, PWM


class Fase:
    def __init__(self, 
                 name:str, 
                 ctx:Context, 
                 target_temp:float | None = None, 
                 target_time:float | None = None, 
                 target_temp_rate:float | None = None, 
                 timeout_limit:float | None = None) -> None:
        self.name = name
        self.ctx = ctx
        self.target_temp = target_temp
        self.target_time = target_time
        self.target_temp_rate = target_temp_rate
        self.timeout_limit= timeout_limit
        self.is_done:bool = False
        self.step_start_time:float = 0.0
        self.step_end_time:float = 0.0
        self.pid:PID | None = None
        self.pwm:PWM = PWM(ctx.ssr_res, frequenza=1.0) #1Hz
        
    
    def check_timeout(self, elapsed:float, max_time:float) -> None:
        if elapsed > max_time:
            raise ErroreTimeout(self.name, elapsed, max_time)
    
    
    def check_temperature(self, elapsed:float, temp:float, target:float) -> None:
        if target*0.9 < temp < target*1.1:
            pass
        else:
            raise ErroreTemperatura(self.name, elapsed, temp, target)


    def print_status(self, elapsed:float, temp:float, progress:float) -> None:
        sys.stdout.write("\033[F\033[K")
        sys.stdout.write("\033[F\033[K")
        sys.stdout.write("\033[F\033[K")

        print(f"{self.name} in corso... Temperatura attuale: {temp:.2f} °C")
        print(f"Tempo trascorso: {time_convert_str(elapsed, ms=False)}")

        lunghezza_barra = 43
        percentuale_barra = max(0, math.floor(lunghezza_barra * progress))
        barra = "█" * percentuale_barra + "_" * (lunghezza_barra - percentuale_barra)
        text = int(progress*100)
        print(f"[{barra}] {text}%")
        #TODO valori real time
        
    
    def set_pid(self, kp, ki, kd, target):
        self.pid = PID(kp, ki, kd, target)
        


class Heating(Fase):
    def __init__(self, 
                 name:str, 
                 ctx:Context, 
                 target_temp:float, 
                 target_time:float, 
                 target_temp_rate:float | None = None, 
                 timeout_limit:float | None = None) -> None:
        super().__init__(name, ctx, target_temp, target_time, target_temp_rate, timeout_limit)
        self.start_temp:float = 0.0


    def run(self):
        self.set_pid(kp=2.0, ki=0.5, kd=1.0, target=self.target_temp)
        self.step_start_time = time.time()
        self.start_temp = last_temp = self.ctx.tc.read_temp_safe()
        last_time:float = 0.0  
        if self.timeout_limit is None:
            self.timeout_limit = (self.target_temp - last_temp) / 0.5 + 20 #TODO per il momento lasciamo 0.5°C/sec + 20 sec
        print(f"{ANSI.BOLD}{ANSI.CYAN}Inizio fase riscaldamento{ANSI.RESET}\n\n\n")
        while not self.is_done:
            elapsed_time = time.time() - self.step_start_time
            delta_time:float = elapsed_time - last_time
            if delta_time > self.ctx.sampling_interval:
                sys_temp = 0 #TODO add dht
                temp = self.ctx.tc.read_temp_safe()
                delta_temp = temp - last_temp
                temp_rate = delta_temp / delta_time
                
                power = self.pid.calcola_output(temp)
                self.pwm.pid_output(power)
            
                if temp < self.target_temp:
                    self.check_timeout(elapsed_time, self.timeout_limit)
                    # self.ctx.ssr_res.turn_on()
                    progress = min((temp - self.start_temp) / (self.target_temp - self.start_temp), 1.0)
                    self.print_status(elapsed_time, temp, progress)
                else:
                    self.ctx.ssr_res.turn_off()
                    self.print_status(elapsed_time, temp, 1.0)
                    print(f"Riscaldamento completato in {time_convert_str(elapsed_time)}.\n\n")
                    self.is_done = True
                    self.step_end_time = time.time()
                    
                last_time = elapsed_time
                last_temp = temp
                self.ctx.sq.add_sample(self.name, 
                                       self.target_temp, 
                                       temp,
                                       self.pid.kp,
                                       self.pid.ki,
                                       self.pid.kd, 
                                       elapsed_time, 
                                       temp_rate, 
                                       self.ctx.ssr_res.get_state(), 
                                       self.ctx.ssr_fan.get_state(),
                                       sys_temp)



class Soaking(Fase):
    def __init__(self, 
                 name:str, 
                 ctx:Context, 
                 target_temp:float, 
                 target_time:float, 
                 timeout_limit:float | None = None) -> None:
        super().__init__(name, ctx, target_temp, target_time, None, timeout_limit)
        
    
    def run(self):
        self.step_start_time = time.time()
        last_temp = self.ctx.tc.read_temp_safe()
        last_time:float = 0.0
        print(f"{ANSI.BOLD}{ANSI.CYAN}Inizio fase mantenimento temperatura...{ANSI.RESET}\n\n\n")
        while not self.is_done:
            elapsed_time = time.time() - self.step_start_time
            delta_time:float = elapsed_time - last_time
            if delta_time > self.ctx.sampling_interval:
                sys_temp = 0 #TODO add dht
                temp = self.ctx.tc.read_temp_safe()
                delta_temp = temp - last_temp
                temp_rate = delta_temp / delta_time
                if temp < self.target_temp:
                    self.ctx.ssr_res.turn_on()
                else:
                    self.ctx.ssr_res.turn_off()
                self.check_temperature(elapsed_time, temp, self.target_temp)
                if elapsed_time < self.target_time:
                    progress = min(elapsed_time / self.target_time, 1.0)
                    self.print_status(elapsed_time, temp, progress)
                else:
                    self.print_status(elapsed_time, temp, 1.0)
                    self.ctx.ssr_res.turn_off()
                    print(f"Essicazione completata in {time_convert_str(elapsed_time)}.\n\n")
                    self.is_done = True
                last_time = elapsed_time
                last_temp = temp
                self.ctx.sq.add_sample(self.name, 
                                       self.target_temp, 
                                       temp, elapsed_time, 
                                       temp_rate, 
                                       self.ctx.ssr_res.get_state(), 
                                       self.ctx.ssr_fan.get_state(), 
                                       sys_temp)
       
      
      
class Cooling(Fase):
    def __init__(self, 
                 name:str, 
                 ctx:Context, 
                 target_temp:float | None, 
                 target_time:float, 
                 target_temp_rate:float | None, 
                 timeout_limit:float | None = None) -> None:
        super().__init__(name, ctx, target_temp, target_time, target_temp_rate, timeout_limit)
        self.start_temp:float = 0.0
        
    
    def run(self):
        self.step_start_time = time.time()
        self.start_temp = last_temp = self.ctx.tc.read_temp_safe()
        last_time:float = 0.0
        print(f"{ANSI.BOLD}{ANSI.CYAN}Inizio fase raffreddamento...\n\n\n{ANSI.RESET}")
        while not self.is_done:
            elapsed_time = time.time() - self.step_start_time
            delta_time:float = elapsed_time - last_time
            if delta_time > self.ctx.sampling_interval:
                sys_temp = 0 #TODO adddht
                temp = self.ctx.tc.read_temp_safe()
                delta_temp = temp - last_temp
                temp_rate = delta_temp / delta_time
                if elapsed_time < self.target_time:
                    #TODO controllo raffreddamento (inseriamo in controllo temperauta?)
                    progress = min(elapsed_time / self.target_time, 1.0)
                    self.print_status(elapsed_time, temp, progress)
                else:
                    self.print_status(elapsed_time, temp, 1.0)
                    self.ctx.ssr_res.turn_off()
                    print(f"Raffreddamento completato in {time_convert_str(elapsed_time)}.\n\n")
                    self.is_done = True
                last_time = elapsed_time
                last_temp = temp
                self.ctx.sq.add_sample(self.name, 
                                       self.target_temp, 
                                       temp, elapsed_time, 
                                       temp_rate, 
                                       self.ctx.ssr_res.get_state(), 
                                       self.ctx.ssr_fan.get_state(), 
                                       sys_temp)