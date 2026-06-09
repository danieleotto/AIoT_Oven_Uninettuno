import time,sys,math
from customlib.functions import time_convert_str
from console_menu import ANSI
from customlib.exceptions import ErroreTemperatura, ErroreTimeout
from context import Context
from pid_pwm import PWM


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
        self.start_temp:float = 0.0
        self.is_done:bool = False
        self.step_start_time:float = 0.0
        self.step_end_time:float = 0.0
        self.pwm_heat:PWM = PWM(self.ctx.ssr_res, frequenza=1.0) #1Hz
        self.pwm_cool:PWM = PWM(self.ctx.ssr_fan, frequenza=1.0) #1Hz
        
    
    def check_timeout(self, elapsed:float, max_time:float) -> None:
        if elapsed > max_time:
            raise ErroreTimeout(self.name, elapsed, max_time)
    
    
    def check_temperature(self, elapsed:float, temp:float, target:float) -> None:
        if target - 25 < temp < target + 25: #TODO aggiornare i limiti temperatura
            pass
        else:
            raise ErroreTemperatura(self.name, elapsed, temp, target)


    def print_status(self,
                     elapsed:float,
                     temp:float,
                     progress:float,
                     res_power:float,
                     fan_power:float,
                     ssr_res_state:str,
                     ssr_fan_state:str,
                     sys_temp:float,
                     power_values:tuple[float, float, float] = (0,0,0)) -> None:
        for i in range (0,7):
            sys.stdout.write("\033[F\033[K")

        print(f"{self.name} in corso...")
        print(f"Tempo trascorso: {time_convert_str(elapsed, ms=False)} | Temperatura: {temp:.1f} °C")

        lunghezza_barra = 43
        percentuale_barra = max(0, math.floor(lunghezza_barra * progress))
        barra = "█" * percentuale_barra + "_" * (lunghezza_barra - percentuale_barra)
        text = max(0, math.floor(progress * 100))
        print(f"[{barra}] {text}%")
        print(f"Temperatura sistema: {sys_temp:.1f}")
        print(f"SSR_Res: state {ssr_res_state} - power {res_power:.2f}")
        print(f"SSR_Fan: state {ssr_fan_state} - power {fan_power:.2f}")
        print(f"Voltage: {power_values[0]:.1f} V | Current: {power_values[1]:.3f} A | Power: {power_values[2]:.1f} W")
        



class Heating(Fase):
    def __init__(self, 
                 name:str, 
                 ctx:Context, 
                 target_temp:float, 
                 target_time:float, 
                 target_temp_rate:float | None = None, 
                 timeout_limit:float | None = None) -> None:
        super().__init__(name, ctx, target_temp, target_time, target_temp_rate, timeout_limit)


    def run(self, prev_step_elapsed_time:float = 0.0) -> float:
        self.ctx.pid.set_pid_target(self.target_temp)
        self.step_start_time = time.time()
        self.start_temp = last_temp = self.ctx.tc.read_temp_safe()
        last_time:float = 0.0
        res_power:float = 0.0
        if self.timeout_limit is None:
            self.timeout_limit = (self.target_temp - last_temp) / 0.5 + 240 #TODO per il momento lasciamo 0.5°C/sec + 240 sec
        print(f"{ANSI.BOLD}{ANSI.CYAN}Inizio fase riscaldamento\n\n\n\n\n\n\n{ANSI.RESET}")
        while not self.is_done:
            elapsed_time = time.time() - self.step_start_time
            delta_time = elapsed_time - last_time
            self.pwm_heat.update(res_power)
            if delta_time > self.ctx.sampling_interval:
                sys_temp = self.ctx.dht22.get_safe_temp()
                temp = self.ctx.tc.read_temp_safe()
                eco2, tvoc = self.ctx.sgp.read()
                delta_temp = temp - last_temp
                temp_rate = delta_temp / delta_time
                
                res_power = self.ctx.pid.calcola_output_limitato_up(temp, temp_rate, self.target_temp_rate)
            
                if temp < self.target_temp:
                    self.check_timeout(elapsed_time, self.timeout_limit)
                    progress = min((temp - self.start_temp) / (self.target_temp - self.start_temp), 1.0)
                    self.print_status(elapsed_time, temp, progress, res_power, 0.0, self.ctx.ssr_res.get_state_str(),
                                      self.ctx.ssr_fan.get_state_str(), sys_temp,
                                      (self.ctx.pzem.get_voltage(), self.ctx.pzem.get_current(), self.ctx.pzem.get_power()),
                                      )
                else:
                    self.ctx.ssr_res.turn_off()
                    self.print_status(elapsed_time, temp, 1.0, res_power, 0.0, self.ctx.ssr_res.get_state_str(),
                                      self.ctx.ssr_fan.get_state_str(), sys_temp,
                                      (self.ctx.pzem.get_voltage(), self.ctx.pzem.get_current(), self.ctx.pzem.get_power()),
                                      )
                    print(f"Riscaldamento completato in {time_convert_str(elapsed_time)}.\n\n")
                    self.is_done = True
                    self.step_end_time = time.time()
                    
                last_time = elapsed_time
                last_temp = temp
                self.ctx.sq.add_sample(self.name, 
                                       self.target_temp,
                                       temp,
                                       (self.target_temp - temp),
                                       self.ctx.pid.kp,
                                       self.ctx.pid.ki,
                                       self.ctx.pid.kd, 
                                       elapsed_time,
                                       elapsed_time + prev_step_elapsed_time,
                                       temp_rate, 
                                       self.ctx.ssr_res.get_state(), 
                                       self.ctx.ssr_fan.get_state(),
                                       sys_temp,
                                       res_power,
                                       self.ctx.pzem.get_voltage(),
                                       self.ctx.pzem.get_current(),
                                       self.ctx.pzem.get_power(),
                                       eco2,
                                       tvoc)
        return last_time + prev_step_elapsed_time




class Soaking(Fase):
    def __init__(self, 
                 name:str, 
                 ctx:Context, 
                 target_temp:float, 
                 target_time:float, 
                 timeout_limit:float | None = None) -> None:
        super().__init__(name, ctx, target_temp, target_time, None, timeout_limit)
    
    
    def run(self, prev_step_elapsed_time:float= 0.0) -> float:
        self.ctx.pid.set_pid_target(self.target_temp)
        self.step_start_time = time.time()
        self.start_temp = last_temp = self.ctx.tc.read_temp_safe()
        last_time:float = 0.0
        res_power:float = 0.0
        print(f"{ANSI.BOLD}{ANSI.CYAN}Inizio fase mantenimento temperatura...\n\n\n\n\n\n\n{ANSI.RESET}")
        while not self.is_done:
            elapsed_time = time.time() - self.step_start_time
            delta_time = elapsed_time - last_time
            self.pwm_heat.update(res_power)
            if delta_time > self.ctx.sampling_interval:
                sys_temp = self.ctx.dht22.get_safe_temp()
                temp = self.ctx.tc.read_temp_safe()
                eco2, tvoc = self.ctx.sgp.read()
                delta_temp = temp - last_temp
                temp_rate = delta_temp / delta_time
                
                res_power = self.ctx.pid.calcola_output(temp)
                
                #self.check_temperature(elapsed_time, temp, self.target_temp)
                if elapsed_time < self.target_time:
                    progress = min(elapsed_time / self.target_time, 1.0)
                    self.print_status(elapsed_time, temp, progress, res_power, 0.0, self.ctx.ssr_res.get_state_str(),
                                      self.ctx.ssr_fan.get_state_str(), sys_temp,
                                      (self.ctx.pzem.get_voltage(), self.ctx.pzem.get_current(), self.ctx.pzem.get_power()),
                                      )
                else:
                    self.print_status(elapsed_time, temp, 1.0, res_power, 0.0, self.ctx.ssr_res.get_state_str(),
                                      self.ctx.ssr_fan.get_state_str(), sys_temp,
                                      (self.ctx.pzem.get_voltage(), self.ctx.pzem.get_current(), self.ctx.pzem.get_power()),
                                      )
                    self.ctx.ssr_res.turn_off()
                    print(f"Essicazione completata in {time_convert_str(elapsed_time)}.\n\n")
                    self.is_done = True
                last_time = elapsed_time
                last_temp = temp
                self.ctx.sq.add_sample(self.name, 
                                       self.target_temp, 
                                       temp,
                                       (self.target_temp - temp),
                                       self.ctx.pid.kp,
                                       self.ctx.pid.ki,
                                       self.ctx.pid.kd,
                                       elapsed_time,
                                       elapsed_time + prev_step_elapsed_time,
                                       temp_rate, 
                                       self.ctx.ssr_res.get_state(), 
                                       self.ctx.ssr_fan.get_state(), 
                                       sys_temp,
                                       res_power,
                                       self.ctx.pzem.get_voltage(),
                                       self.ctx.pzem.get_current(),
                                       self.ctx.pzem.get_power(),
                                       eco2,
                                       tvoc)
        return last_time + prev_step_elapsed_time
       
      
      
      
class Cooling(Fase):
    def __init__(self, 
                 name:str, 
                 ctx:Context, 
                 target_temp:float, 
                 target_time:float, 
                 target_temp_rate:float | None, 
                 timeout_limit:float | None = None) -> None:
        super().__init__(name, ctx, target_temp, target_time, target_temp_rate, timeout_limit)
        
    
    def run(self, prev_step_elapsed_time:float = 0.0) -> float:
        self.ctx.pid.set_pid_target(self.target_temp)
        self.step_start_time = time.time()
        self.start_temp = last_temp = self.ctx.tc.read_temp_safe()
        last_time:float = 0.0
        res_power:float = 0.0
        print(f"{ANSI.BOLD}{ANSI.CYAN}Inizio fase raffreddamento...\n\n\n\n\n\n\n{ANSI.RESET}")
        while not self.is_done:
            elapsed_time = time.time() - self.step_start_time
            delta_time = elapsed_time - last_time
            self.pwm_heat.update(res_power)
            if delta_time > self.ctx.sampling_interval:
                sys_temp = self.ctx.dht22.get_safe_temp()
                temp = self.ctx.tc.read_temp_safe()
                eco2, tvoc = self.ctx.sgp.read()
                delta_temp = temp - last_temp
                temp_rate = delta_temp / delta_time
                
                res_power = self.ctx.pid.calcola_output_limitato_down(temp, temp_rate, self.target_temp_rate)
                #TODO ventola?
                
                if elapsed_time < self.target_time:
                    progress = min(elapsed_time / self.target_time, 1.0)
                    self.print_status(elapsed_time, temp, progress, res_power, 0.0, self.ctx.ssr_res.get_state_str(),
                                      self.ctx.ssr_fan.get_state_str(), sys_temp,
                                      (self.ctx.pzem.get_voltage(), self.ctx.pzem.get_current(), self.ctx.pzem.get_power()),
                                      )
                else:
                    self.print_status(elapsed_time, temp, 1.0, res_power, 0.0, self.ctx.ssr_res.get_state_str(),
                                      self.ctx.ssr_fan.get_state_str(), sys_temp,
                                      (self.ctx.pzem.get_voltage(), self.ctx.pzem.get_current(), self.ctx.pzem.get_power()),
                                      )
                    self.ctx.ssr_res.turn_off()
                    print(f"Raffreddamento completato in {time_convert_str(elapsed_time)}.\n\n")
                    self.is_done = True
                last_time = elapsed_time
                last_temp = temp
                self.ctx.sq.add_sample(self.name, 
                                       self.target_temp, 
                                       temp,
                                       (self.target_temp - temp),
                                       self.ctx.pid.kp,
                                       self.ctx.pid.ki,
                                       self.ctx.pid.kd,
                                       elapsed_time,
                                       elapsed_time + prev_step_elapsed_time,
                                       temp_rate, 
                                       self.ctx.ssr_res.get_state(), 
                                       self.ctx.ssr_fan.get_state(), 
                                       sys_temp,
                                       res_power,
                                       self.ctx.pzem.get_voltage(),
                                       self.ctx.pzem.get_current(),
                                       self.ctx.pzem.get_power(),
                                       eco2,
                                       tvoc)
        return last_time + prev_step_elapsed_time