import os, time, json, sys
from console_menu import TextMenu, ANSI
from functools import partial
from customlib.functions import todo_placeholder, get_timestamp, time_convert_str, clear_console
from customlib.classes import ErroreTimeout, ErroreTemperatura, ErroreSonda
from main import Context


def print_title(title:str) -> None:
    print("\n"+"="*50)
    print(f"{ANSI.BOLD}{ANSI.MAGENTA}{title}{ANSI.RESET}")
    print("="*50)


def clear_values(params:dict) -> None:
    try:
        for key,val in params.items():
            params[key] = None
    except:
        input("Errore cancellando i dati...")
    
        
def load_presets(self, preset_file:str, menu:TextMenu) -> None:
    #TODO presetFile type
    #file = preset_file
    filename = os.path.join("presets", preset_file)
    with open(filename) as fn:
        presets = json.load(fn)            
    for item in presets["values"]:
        if item is presets["values"][-1]:
            menu.add_option(item["id"], item["name"]+"\n", partial(self.set_value_from_preset, item))
        else:
            menu.add_option(item["id"], item["name"], partial(self.set_value_from_preset, item))
  
        
def is_complete(obj):
    #TODO types (considerare di fare una classe processi)
    return all(v is not None for v in obj.params.values())


def print_status(step:str, elapsed:float, temp:float, progress:float) -> None:
    sys.stdout.write("\033[F\033[K")
    sys.stdout.write("\033[F\033[K")
    sys.stdout.write("\033[F\033[K")

    print(f"{step} in corso... Temperatura attuale: {temp:.2f} °C")
    print(f"Tempo trascorso: {time_convert_str(elapsed, ms=True)}")

    lunghezza_barra = 50
    percentuale_barra = int(lunghezza_barra * progress)
    barra = "█" * percentuale_barra + "_" * (lunghezza_barra - percentuale_barra)
    text = int(progress*100)
    print(f"[{barra}] {text}%")


def check_timeout(elapsed:float, max_time:float, step:str) -> None:
    if elapsed > max_time:
        raise ErroreTimeout(step, elapsed, max_time)


def check_temperature(elapsed:float, temp:float, target:float, step:str) -> None:
    if target*0.9 < temp < target*1.1:
        pass
    else:
        raise ErroreTemperatura(step, elapsed, temp, target)
   
   
def check_tc(result):
    #TODO result filetype
    if result is None:
        raise ErroreSonda
    else:
        return result
    
    
class Essicatura:
    """Gestisce il processo di essicatura."""
    def __init__(self, ctx:Context) -> None:
        self.params = {
            "target_temp": None,
            "heat_time": None
        }
        self.ctx = ctx
        self.process_name = "Essicatura"
        self.process_menu = TextMenu("                --- ESSICATURA ---", color_title=ANSI.MAGENTA, color_option=ANSI.CYAN)
        self.preset_menu = TextMenu("            --- PRESET ESSICATURA ---", color_title=ANSI.CYAN, color_option=ANSI.WHITE)
        self.process_menu.add_option("P", "Presets di Essicatura\n",self.preset_menu)
        self.process_menu.add_option("1", lambda: f"Imposta Target Temp.: {self.params['target_temp'] or '-'} [°C]", partial(self._set_value, "target_temp", "Target temperatura [°C]: "))
        self.process_menu.add_option("2", lambda: f"Imposta Durata      : {time_convert_str(self.params['heat_time']) or '- [s]'}", partial(self._set_value,"heat_time","Durata essicatura [s]: "))
        self.process_menu.add_option("A", "Avvia", self.run, disabled=True, executable=True)
        #TODO se esiste file preset carica
        load_presets(self,"essicatura.json",self.preset_menu)
        self.preset_menu.add_option("C", "Crea preset ", todo_placeholder)
     
         
    def _set_value(self, value, message) -> None:
        try:
            v = float(input(message))
            self.params[value] = v
            if is_complete(self):
                self.process_menu.enable_exec()
        except:
            print("Valore non valido.")
            input("Invio per continuare...")
    
    
    def _set_value_from_preset(self, item):
        self.params["target_temp"] = item["target_temp"]
        self.params["heat_time"] = item["heat_time"]
        if is_complete(self):
            self.process_menu.enable_exec()
        print("Preset caricato...")
        time.sleep(0.5)
        return "BACK"
        
    
    def run(self) -> str:
        #TODO completare logica
        steps = {"heating":False, "dehydrating": False}
        timestamp = get_timestamp(readable=False)
        t = self.params["target_temp"]
        ti = self.params["heat_time"]
        last_time:float = 0.0
        
        self.ctx.sq.add_process(timestamp, self.process_name)
        try:
            clear_console()
            print_title(self.process_menu.title)
            print("Press CTRL+C per interrompere il processo.\n")
            last_temp = self.ctx.tc.controllo_sonda(self.ctx.sampling_interval)
            start_time = heating_start_time = time.time()
            MAX_TIME:float = (t - last_temp) / 0.5 #per il momento lasciamo 0.5 grado/secondo come limite minimo di riscaldamento (per scaldarsi 50 gradi ha a disposiizone max 50 secondi)
            print(f"{ANSI.BOLD}{ANSI.CYAN}Inizio fase riscaldamento...{ANSI.RESET}\n\n\n")
            while not steps["heating"]:
                elapsed_time = time.time() - heating_start_time
                delta_time:float = elapsed_time - last_time
                if delta_time > self.ctx.sampling_interval:
                    sys_temp = 0 #TODO add dht
                    temp = self.ctx.tc.read_temp_average()
                    delta_temp = temp - last_temp
                    temp_rate = delta_temp / delta_time
                    if temp < t:
                        check_timeout(elapsed_time, MAX_TIME, "Riscaldamento")
                        self.ctx.ssr_res.HIGH()
                        progress = min(temp / t, 1.0)
                        print_status("Riscaldamento", elapsed_time, temp, progress)
                        #TODO aggiungere il safetyoff se maxtime è superato, al momento off per debug
                    else:
                        self.ctx.ssr_res.LOW()
                        print_status("Riscaldamento", elapsed_time, temp, 1.0)
                        print(f"Riscaldamento completato in {time_convert_str(elapsed_time)}.\n\n")
                        steps["heating"] = True
                    last_time = elapsed_time
                    last_temp = temp
                    self.ctx.sq.add_sample("heating", t, temp, elapsed_time, temp_rate, self.ctx.ssr_res.get_state(), self.ctx.ssr_fan.get_state(),sys_temp)
                    
            dehydr_start_time = time.time()
            elapsed_time = 0
            last_time = 0
            last_temp = self.ctx.tc.read_temp_average()
            print(f"{ANSI.BOLD}{ANSI.CYAN}Inizio fase essicazione...{ANSI.RESET}\n\n\n")
            while not steps["dehydrating"]:
                elapsed_time = time.time() - dehydr_start_time
                delta_time = elapsed_time - last_time
                if delta_time > self.ctx.sampling_interval:
                    sys_temp = 0 #TODO add dht
                    temp = self.ctx.tc.read_temp_average()
                    delta_temp = temp - last_temp
                    temp_rate = delta_temp / delta_time
                    if temp < t:
                        self.ctx.ssr_res.HIGH()
                    else:
                        self.ctx.ssr_res.LOW()
                    check_temperature(elapsed_time, temp, t, "Essicatura")
                    if elapsed_time < ti:
                        progress = min(elapsed_time / ti, 1.0)
                        print_status(self.process_name, elapsed_time, temp, progress)
                    else:
                        print_status(self.process_name, elapsed_time, temp, 1.0)
                        self.ctx.ssr_res.LOW()
                        print(f"Essicazione completata in {time_convert_str(elapsed_time)}.\n\n")
                        steps["dehydrating"] = True
                    last_time = elapsed_time
                    last_temp = temp
                    self.ctx.sq.add_sample("dehydrating", t, temp, elapsed_time, temp_rate, self.ctx.ssr_res.get_state(), self.ctx.ssr_fan.get_state(), sys_temp)
            
            process_time = time.time() - start_time
            self.ctx.ssr_res.LOW()
            self.ctx.ssr_fan.LOW()
            self.ctx.sq.process_complete(process_time, "OK")
            self.ctx.sq.log_samples()
            clear_values(self.params)
            input(f"{ANSI.BOLD}{ANSI.GREEN}Processo completato in {time_convert_str(process_time)}.\nPremere un tasto per continuare...{ANSI.RESET}\n")    
            return "MAIN_MENU"
                
        except KeyboardInterrupt:
            process_time = time.time() - start_time
            self.ctx.ssr_res.LOW()
            self.ctx.ssr_fan.LOW()
            self.ctx.sq.process_complete(process_time, "USER_STOP")
            self.ctx.sq.log_samples()
            clear_values(self.params)
            input(f"\n{ANSI.BOLD}{ANSI.RED}Processo terminato dall'utente.\nPremere un tasto per continuare...{ANSI.RESET}")
            return "MAIN_MENU"

        except ErroreTimeout as e:
            process_time = time.time() - start_time
            self.ctx.ssr_res.LOW()
            self.ctx.ssr_fan.LOW()
            self.ctx.sq.process_complete(process_time, "TIMEOUT_ERROR")
            self.ctx.sq.log_samples()
            clear_values(self.params)
            print(f"{ANSI.BOLD}{ANSI.RED}ERRORE: Timeout nella fase {e.step}.\nTempo trascorso: {time_convert_str(e.elapsed, ms=True)}")
            print(f"- Il forno non ha raggiunto la temperatura target nel tempo massimo di {time_convert_str(e.max_time)}{ANSI.RESET}")
            input("Premere un tasto per continuare...")
            return "MAIN_MENU"

        except ErroreTemperatura as e:
            process_time = time.time() - start_time
            self.ctx.ssr_res.LOW()
            self.ctx.ssr_fan.LOW()
            self.ctx.sq.process_complete(process_time, "TEMP_ERROR")
            self.ctx.sq.log_samples()
            clear_values(self.params)
            print(f"{ANSI.BOLD}{ANSI.RED}ERRORE: Temperatura non stabile nella fase {e.step}.\nTempo trascorso: {time_convert_str(e.elapsed, ms=True)}")
            print(f"- La temperatura rilevata eccede il 10% di tolleranza.\nRilevata: {e.temp:.2f}°C - Target: {e.target:.2f}°C{ANSI.RESET}")
            input("Premere un tasto per continuare...")
            return "MAIN_MENU"
        
        except ErroreSonda as e:
            self.ctx.ssr_res.LOW()
            self.ctx.ssr_fan.LOW()
            clear_values(self.params)
            print(f"{ANSI.BOLD}{ANSI.RED}ERRORE: Sonda non rilevata.{ANSI.RESET}")
            input("Premere un tasto per continuare...")
            return "MAIN_MENU"


class Ricottura:
    """Gestisce il processo di ricottura."""
    def __init__(self, ctx:Context) -> None:
        self.params = {
            "target_temp": None,
            "reheat_duration": None,
            "cooling_rate": None,
            "cooling_time_calc": None
        }
        self.ctx = ctx
        self.process_name = "Ricottura"
        self.process_menu = TextMenu("                 --- RICOTTURA ---", color_title=ANSI.MAGENTA, color_option=ANSI.CYAN)
        self.preset_menu = TextMenu("             --- PRESET RICOTTURA ---", color_title=ANSI.CYAN, color_option=ANSI.WHITE)
        self.process_menu.add_option("P", "Presets di Ricottura\n",self.preset_menu)
        self.process_menu.add_option("1", lambda: f"Imposta Target Temp.: {self.params['target_temp'] or '-'} [°C]", partial(self._set_value, "target_temp", "Target temperatura [°C]: "))
        self.process_menu.add_option("2", lambda: f"Imposta Heat Time   : {time_convert_str(self.params['reheat_duration']) or '- [s]'}", partial(self._set_value, "reheat_duration", "Durata ricottura [s]: "))
        self.process_menu.add_option("3", lambda: f"Imposta Cooling Rate: {self.params['cooling_rate'] or '-'} [°C/s]\n    Cooling time        : {time_convert_str(self.params['cooling_time_calc']) or '- [s]'}", partial(self._set_value, "cooling_rate","Rate raffreddamento [°C/s]: "))
        self.process_menu.add_option("A", "Avvia", self.run, disabled=True, executable=True)
        #TODO se esiste file preset carica
        load_presets(self, "ricottura.json", self.preset_menu)
        self.preset_menu.add_option("C", "Crea preset ", todo_placeholder)
     
        
    def _set_value(self, value, message):
        try:
            v = float(input(message))
            self.params[value] = v
            if self.params["cooling_rate"] and self.params["target_temp"]:
                self.params["cooling_time_calc"] = round((self.params["target_temp"] - 20) / self.params["cooling_rate"])
            if is_complete(self):
                self.process_menu.enable_exec()
        except:
            print("Valore non valido.")
            print("Invio per continuare...")
    
    
    def set_value_from_preset(self, item):
        self.params["target_temp"] = item["target_temp"]
        self.params["reheat_duration"] = item["reheat_duration"]
        self.params["cooling_rate"] = item["cooling_rate"]
        if self.params["cooling_rate"] and self.params["target_temp"]:
            self.params["cooling_time_calc"] = round((self.params["target_temp"] - 20) / self.params["cooling_rate"])
        if is_complete(self):
            self.process_menu.enable_exec()
        print("Preset caricato...")
        time.sleep(0.5)
        return "BACK"
        
    
    def run(self) -> str:
        steps = {"heating":False, "soaking": False, "cooling": False}
        timestamp = get_timestamp(readable=False)
        t = self.params["target_temp"]
        sti = self.params["reheat_duration"]
        cr = self.params["cooling_rate"] #TODO
        cti = self.params["cooling_time_calc"]
        elapsed_time = 0
        last_time = 0
        
        self.ctx.sq.add_process(timestamp, self.process_name)
        try:
            clear_console()
            print_title(self.process_menu.title)
            print("Premi CTRL+C per interrompere il processo.\n")
            last_temp = self.ctx.tc.controllo_sonda(self.ctx.sampling_interval)
            start_time = heat_start_time = time.time()
            MAX_TIME:float = (t - last_temp) / 0.5 #vedi commento su essicatura
            print(f"{ANSI.BOLD}{ANSI.CYAN}Inizio fase riscaldamento...\n\n\n{ANSI.RESET}")
            while not steps["heating"]:
                elapsed_time = time.time() - heat_start_time
                delta_time = elapsed_time - last_time
                if delta_time > self.ctx.sampling_interval:
                    sys_temp = 0 #TODO add dht
                    temp = self.ctx.tc.read_temp_average()
                    delta_temp = temp - last_temp
                    temp_rate = delta_temp / delta_time
                    if temp < t:
                        check_timeout(elapsed_time, MAX_TIME, "Riscaldamento")
                        self.ctx.ssr_res.HIGH()
                        progress = min(temp / t, 1.0)
                        print_status("Riscaldamento", elapsed_time, temp, progress)
                        #TODO aggiungere il safetyoff se maxtime è superato, al momento off per debug
                    else:
                        self.ctx.ssr_res.LOW()
                        print_status("Riscaldamento", elapsed_time, temp, 1.0)
                        print(f"Riscaldamento completato in {time_convert_str(elapsed_time)}.\n\n")
                        steps["heating"] = True
                    last_time = elapsed_time
                    last_temp = temp
                    self.ctx.sq.add_sample("heating", t, temp, elapsed_time, temp_rate, self.ctx.ssr_res.get_state(), self.ctx.ssr_fan.get_state(), sys_temp)
                
            soak_start_time = time.time()
            elapsed_time = 0
            last_time = 0
            last_temp = self.ctx.tc.read_temp_average()
            print(f"{ANSI.BOLD}{ANSI.CYAN}Inizio fase mantenimento temperatura...\n\n\n{ANSI.RESET}")
            while not steps["soaking"]:
                elapsed_time = time.time() - soak_start_time
                delta_time = elapsed_time - last_time
                if delta_time > self.ctx.sampling_interval:
                    sys_temp = 0 #TODO add dht
                    temp = self.ctx.tc.read_temp_average()
                    delta_temp = temp - last_temp
                    temp_rate = delta_temp / delta_time
                    if temp < t:
                        self.ctx.ssr_res.HIGH()
                    else:
                        self.ctx.ssr_res.LOW()
                    check_temperature(elapsed_time, temp, t, "Ricottura")
                    if elapsed_time < sti:
                        progress = min(elapsed_time/sti, 1.0)
                        print_status("Ricottura", elapsed_time, temp, progress)
                    else:
                        print_status("Ricottura", elapsed_time, temp, 1.0)
                        self.ctx.ssr_res.LOW()
                        print(f"Ricottura completata in {time_convert_str(elapsed_time)}.\n\n")
                        steps["soaking"] = True
                    last_time = elapsed_time
                    last_temp = temp
                    self.ctx.sq.add_sample("soaking", t, temp, elapsed_time, temp_rate, self.ctx.ssr_res.get_state(), self.ctx.ssr_fan.get_state(), sys_temp)
                
            cooling_start_time = time.time()
            elapsed_time = 0
            last_time = 0
            last_temp = self.ctx.tc.read_temp_average()
            print(f"{ANSI.BOLD}{ANSI.CYAN}Inizio fase raffreddamento...\n\n\n{ANSI.RESET}")
            while not steps["cooling"]:
                elapsed_time = time.time() - cooling_start_time
                delta_time = elapsed_time - last_time
                if delta_time > self.ctx.sampling_interval:
                    sys_temp = 0 #TODO adddht
                    temp = self.ctx.tc.read_temp_average()
                    delta_temp = temp - last_temp
                    temp_rate = delta_temp / delta_time
                    if elapsed_time < cti:
                        #TODO controllo raffreddamento (inseriamo in controllo temperauta?)
                        progress = min(elapsed_time / cti, 1.0)
                        print_status("Raffreddamento", elapsed_time, temp, progress)
                    else:
                        print_status("Raffreddamento", elapsed_time, temp, 1.0)
                        self.ctx.ssr_res.LOW()
                        print(f"Raffreddamento completato in {time_convert_str(elapsed_time)}.\n\n")
                        steps["cooling"] = True
                    last_time = elapsed_time
                    last_temp = temp
                    self.ctx.sq.add_sample("cooling", t, temp, elapsed_time, temp_rate, self.ctx.ssr_res.get_state(), self.ctx.ssr_fan.get_state(), sys_temp)
                    
            process_time = time.time() - start_time
            self.ctx.ssr_res.LOW()
            self.ctx.ssr_fan.LOW()
            self.ctx.sq.process_complete(process_time, "OK")
            self.ctx.sq.log_samples()
            clear_values(self.params)
            input(f"{ANSI.BOLD}{ANSI.GREEN}Processo completato in {time_convert_str(process_time)}.\nPremere un tasto per continuare...{ANSI.RESET}")
            return "MAIN_MENU"
        
        except KeyboardInterrupt:
            process_time = time.time() - start_time
            self.ctx.ssr_res.LOW()
            self.ctx.ssr_fan.LOW()
            self.ctx.sq.process_complete(process_time, "USER_STOP")
            self.ctx.sq.log_samples()
            clear_values(self.params)
            input(f"\n{ANSI.BOLD}{ANSI.RED}Processo terminato dall'utente.\nPremere un tasto per continuare...{ANSI.RESET}")
            return "MAIN_MENU"

        except ErroreTimeout as e:
            process_time = time.time() - start_time
            self.ctx.ssr_res.LOW()
            self.ctx.ssr_fan.LOW()
            self.ctx.sq.process_complete(process_time, "TIMEOUT_ERROR")
            self.ctx.sq.log_samples()
            clear_values(self.params)
            print(f"{ANSI.BOLD}{ANSI.RED}ERRORE: Timeout nella fase {e.step}.\nTempo trascorso: {time_convert_str(e.elapsed, ms=True)}")
            print(f"- Il forno non ha raggiunto la temperatura target nel tempo massimo di {time_convert_str(e.max_time)}{ANSI.RESET}")
            input("Premere un tasto per continuare...")
            return "MAIN_MENU"

        except ErroreTemperatura as e:
            process_time = time.time() - start_time
            self.ctx.ssr_res.LOW()
            self.ctx.ssr_fan.LOW()
            self.ctx.sq.process_complete(process_time, "TEMP_ERROR")
            self.ctx.sq.log_samples()
            clear_values(self.params)
            print(f"{ANSI.BOLD}{ANSI.RED}ERRORE: Temperatura non stabile nella fase {e.step}.\nTempo trascorso: {time_convert_str(e.elapsed, ms=True)}")
            print(f"- La temperatura rilevata eccede il 10% di tolleranza.\nRilevata: {e.temp:.2f}°C - Target: {e.target:.2f}°C{ANSI.RESET}")
            input("Premere un tasto per continuare...")
            return "MAIN_MENU"
        
        except ErroreSonda as e:
            self.ctx.ssr_res.LOW()
            self.ctx.ssr_fan.LOW()
            clear_values(self.params)
            return "MAIN_MENU"



class SaldaturaSMD:
    """Gestisce il processo di saldatura SMD per reflow."""
    def __init__(self, ctx:Context) -> None:
        self.params = {
            "ph_temp": None,
            "ph_rate": None,
            "ph_time_calc": None,
            "soak_temp_calc": None,
            "soak_time": None,
            "reflow_temp": None,
            "reflow_rate": None,
            "reflow_time_calc": None,
            "reflow_peak_time": None,
            "cooling_rate": None,
            "cooling_time_calc": None,           
        }
        self.ctx = ctx
        self.process_name = "Saldatura"
        self.process_menu = TextMenu("              --- SALDATURA SMD ---", color_title=ANSI.MAGENTA, color_option=ANSI.CYAN)
        self.preset_menu = TextMenu("           --- PRESET SALDATURA SMD ---", color_title=ANSI.CYAN, color_option=ANSI.WHITE)
        self.process_menu.add_option("P", "Presets di Saldatura SMD\n",self.preset_menu)
        self.process_menu.add_option("1", lambda: f"Imposta Pre-Heat temp   : {self.params['ph_temp'] or '-'} [°C]", partial(self._set_value,"ph_temp","Target temperatura [°C]: "))
        self.process_menu.add_option("2", lambda: f"Imposta Pre-Heat rate   : {self.params['ph_rate'] or '-'} [°C/s]\n    Pre-Heat time           : {time_convert_str(self.params['ph_time_calc']) or '- [s]'}", partial(self._set_value,"ph_rate","Target rate [°C/s]: "))
        self.process_menu.add_option("3", lambda: f"Imposta Soak time       : {time_convert_str(self.params['soak_time']) or '- [s]'}", partial(self._set_value,"soak_time","Tempo soak [s]: "))
        self.process_menu.add_option("4", lambda: f"Imposta Reflow temp     : {self.params['reflow_temp'] or '-'} [°C]", partial(self._set_value,"reflow_temp","Target temperatura [°C]: "))
        self.process_menu.add_option("5", lambda: f"Imposta Reflow rate     : {self.params['reflow_rate'] or '-'} [°C/s]\n    Reflow time             : {time_convert_str(self.params['reflow_time_calc']) or '- [s]'}", partial(self._set_value,"reflow_rate","Target rate [°C/s]: "))
        self.process_menu.add_option("6", lambda: f"Imposta Reflow peak time: {time_convert_str(self.params['reflow_peak_time']) or '- [s]'}", partial(self._set_value,"reflow_peak_time","Tempo peak [°C]: "))
        self.process_menu.add_option("7", lambda: f"Imposta Cooling rate    : {self.params['cooling_rate'] or '-'} [°C/s]\n    Cooling time            : {time_convert_str(self.params['cooling_time_calc']) or '- [s]'}", partial(self._set_value,"cooling_rate","Target rate [s]: "))
        self.process_menu.add_option("A", "Avvia", self.run, disabled=True, executable=True)
        #TODO se esiste file preset carica
        load_presets(self, "saldatura.json", self.preset_menu)
        self.preset_menu.add_option("C", "Crea preset ", todo_placeholder)
     
        
    def _set_value(self, value, message):
        try:
            v = float(input(message))
            self.params[value] = v
            
            if self.params["ph_temp"] and self.params["ph_rate"]:
                self.params["ph_time_calc"] = round((self.params["ph_temp"] - 20) / self.params["ph_rate"])
            if self.params["ph_temp"]:
                self.params["soak_temp_calc"] = self.params["ph_temp"]
            if self.params["reflow_temp"] and self.params["reflow_rate"] and self.params["soak_temp_calc"]:
                self.params["reflow_time_calc"] = round((self.params["reflow_temp"] - self.params["soak_temp_calc"]) / self.params["reflow_rate"])
            if self.params["reflow_temp"] and self.params["cooling_rate"]:
                self.params["cooling_time_calc"] = round((self.params["reflow_temp"] - 20) / self.params["cooling_rate"])

            if is_complete(self):
                self.process_menu.enable_exec()
        except:
            print("Valore non valido.")
            print("Invio per continuare...")
    
    
    def set_value_from_preset(self, item):
        self.params["ph_temp"] = item["ph_temp"]
        self.params["ph_rate"] = item["ph_rate"]
        self.params["soak_time"] = item["soak_time"]
        self.params["reflow_temp"] = item["reflow_temp"]
        self.params["reflow_rate"] = item["reflow_rate"]
        self.params["reflow_peak_time"] = item["reflow_peak_time"]
        self.params["cooling_rate"] = item["cooling_rate"]

        if self.params["ph_temp"] and self.params["ph_rate"]:
            self.params["ph_time_calc"] = round((self.params["ph_temp"] - 20) / self.params["ph_rate"])
        if self.params["ph_temp"]:
            self.params["soak_temp_calc"] = self.params["ph_temp"]
        if self.params["reflow_temp"] and self.params["reflow_rate"] and self.params["soak_temp_calc"]:
            self.params["reflow_time_calc"] = round((self.params["reflow_temp"] - self.params["soak_temp_calc"]) / self.params["reflow_rate"])
        if self.params["reflow_temp"] and self.params["cooling_rate"]:
            self.params["cooling_time_calc"] = round((self.params["reflow_temp"] - 20) / self.params["cooling_rate"])

        if is_complete(self):
            self.process_menu.enable_exec()
        print("Preset caricato...")
        time.sleep(0.5)
        return "BACK"
        
    
    def run(self) -> str:
        steps = {"preheating":False, "soaking":False, "reflowheat":False, "reflow":False, "cooling":False}
        timestamp = get_timestamp(readable=False)
        pt = self.params["ph_temp"]
        pr = self.params["ph_rate"]
        pti = self.params["ph_time_calc"]
        st = self.params["soak_temp_calc"]
        sti = self.params["soak_time"]
        rt = rpt = self.params["reflow_temp"]
        rr = self.params["reflow_rate"]
        rti = self.params["reflow_time_calc"]
        rpti = self.params["reflow_peak_time"]
        cr = self.params["cooling_rate"]
        cti = self.params["cooling_time_calc"]
        elapsed_time = 0
        last_time = 0
        
        self.ctx.sq.add_process(timestamp, self.process_name)
        try:
            clear_console()
            print_title(self.process_menu.title)
            print("Premi CTRL+C per interrompere il processo.\n")
            last_temp = self.ctx.tc.controllo_sonda(self.ctx.sampling_interval)
            start_time = preheat_start_time = time.time()
            MAX_TIME:float = (pt - last_temp) / 0.5 #vedi commento su essicatura
            print(f"{ANSI.BOLD}{ANSI.CYAN}Inizio fase riscaldamento per pre-heat...\n\n\n{ANSI.RESET}")
            while not steps["preheating"]:
                elapsed_time = time.time() - preheat_start_time
                delta_time = elapsed_time - last_time
                if delta_time > self.ctx.sampling_interval:
                    sys_temp = 0 #TODO add dht
                    temp = self.ctx.tc.read_temp_average()
                    delta_temp = temp - last_temp
                    temp_rate = delta_temp / delta_time
                    if temp < pt:
                        check_timeout(elapsed_time, MAX_TIME, "Pre-Heating")
                        self.ctx.ssr_res.HIGH()
                        progress = min(temp / pt, 1.0)
                        print_status("Pre-Heating", elapsed_time, temp, progress)
                        #TODO aggiungere il sfatyoff se maxtime superato
                    else:
                        self.ctx.ssr_res.LOW()
                        print_status("Pre-Heating", elapsed_time, temp, 1.0)
                        print(f"Pre-Heating completato in {time_convert_str(elapsed_time)}.\n\n")
                        steps["preheating"] = True
                    last_time = elapsed_time
                    last_temp = temp
                    self.ctx.sq.add_sample("preheating", pt, temp, elapsed_time, temp_rate, self.ctx.ssr_res.get_state(), self.ctx.ssr_fan.get_state(), sys_temp)
                    
            soak_start_time = time.time()
            elapsed_time = 0
            last_time = 0
            last_temp = self.ctx.tc.read_temp_average()
            print(f"{ANSI.BOLD}{ANSI.CYAN}Inizio fase mantenimento temperatura...\n\n\n{ANSI.RESET}")
            while not steps["soaking"]:
                elapsed_time = time.time() - soak_start_time
                delta_time = elapsed_time - last_time
                if delta_time > self.ctx.sampling_interval:
                    sys_temp = 0 #TODO add dht
                    temp = self.ctx.tc.read_temp_average()
                    delta_temp = temp - last_temp
                    temp_rate = delta_temp / delta_time
                    if temp < st:
                        self.ctx.ssr_res.HIGH()
                    else:
                        self.ctx.ssr_res.LOW()
                    check_temperature(elapsed_time, temp, st, "Soaking")
                    if elapsed_time < sti:
                        progress = elapsed_time/sti
                        print_status("Soaking", elapsed_time, temp, progress)
                    else:
                        print_status("Soaking", elapsed_time, temp, 1.0)
                        self.ctx.ssr_res.LOW()
                        print(f"Soaking completato in {time_convert_str(elapsed_time)}.\n\n")
                        steps["soaking"] = True
                    last_time = elapsed_time
                    last_temp = temp
                    self.ctx.sq.add_sample("soaking", st, temp, elapsed_time, temp_rate, self.ctx.ssr_res.get_state(), self.ctx.ssr_fan.get_state(), sys_temp)
            
            reflow_start_time = time.time()
            elapsed_time = 0
            last_time = 0
            last_temp = self.ctx.tc.read_temp_average()
            MAX_TIME:float = (rt - last_temp) / 0.5
            print(f"{ANSI.BOLD}{ANSI.CYAN}Inizio fase reflow...\n\n\n{ANSI.RESET}")
            while not steps["reflowheat"]:
                elapsed_time = time.time() - reflow_start_time
                delta_time = elapsed_time - last_time
                if delta_time > self.ctx.sampling_interval:
                    sys_temp = 0 #TODO add dht
                    temp = self.ctx.tc.read_temp_average()
                    delta_temp = temp - last_temp
                    temp_rate = delta_temp / delta_time
                    if temp < rt:
                        check_timeout(elapsed_time, MAX_TIME, "Reflow Heating")
                        self.ctx.ssr_res.HIGH()
                        progress = min(temp / rt, 1.0)
                        print_status("Reflow Heating", elapsed_time, temp, progress)
                        #TODO safetyoff
                    else:
                        self.ctx.ssr_res.LOW()
                        print_status("Reflow Heating", elapsed_time, temp, 1.0)
                        print(f"Reflow Heating completato in {time_convert_str(elapsed_time)}.\n\n")
                        steps["reflowheat"] = True
                    last_time = elapsed_time
                    last_temp = temp
                    self.ctx.sq.add_sample("reflow_heat", rt, temp, elapsed_time, temp_rate, self.ctx.ssr_res.get_state(), self.ctx.ssr_fan.get_state(),sys_temp)                   
            
            reflow_peak_start_time = time.time()
            elapsed_time = 0
            last_time = 0
            last_temp = self.ctx.tc.read_temp_average()
            print(f"{ANSI.BOLD}{ANSI.CYAN}Inizio fase picco reflow...{ANSI.RESET}\n\n\n")
            while not steps["reflow"]:
                elapsed_time = time.time() - reflow_peak_start_time
                delta_time = elapsed_time - last_time
                if delta_time > self.ctx.sampling_interval:
                    sys_temp = 0 #TODO add dht
                    temp = self.ctx.tc.read_temp_average()
                    delta_temp = temp - last_temp
                    temp_rate = delta_temp / delta_time
                    if temp < rpt:
                        self.ctx.ssr_res.HIGH()
                    else:
                        self.ctx.ssr_res.LOW()
                    check_temperature(elapsed_time, temp, rpt, "Reflow Peak")
                    if elapsed_time < rpti:
                        progress = min(elapsed_time / rpti, 1.0)
                        print_status("Reflow Peak", elapsed_time, temp, progress)
                    else:
                        print_status("Reflow Peak", elapsed_time, temp, 1.0)
                        self.ctx.ssr_res.LOW()
                        print(f"Reflow Peak completato in {time_convert_str(elapsed_time)}.\n\n")
                        steps["reflow"] = True
                    last_time = elapsed_time
                    last_temp = temp
                    self.ctx.sq.add_sample("reflow", rpt, temp, elapsed_time, temp_rate, self.ctx.ssr_res.get_state(), self.ctx.ssr_fan.get_state(), sys_temp)
            
            cooling_start_time = time.time()
            elapsed_time = last_time = 0
            last_temp = self.ctx.tc.read_temp_average()
            print(f"{ANSI.BOLD}{ANSI.CYAN}Inizio fase raffreddamento...\n\n\n{ANSI.RESET}")
            while not steps["cooling"]:
                elapsed_time = time.time() - cooling_start_time
                delta_time = elapsed_time - last_time
                if delta_time > self.ctx.sampling_interval:
                    sys_temp = 0 #TODO add dht
                    temp = self.ctx.tc.read_temp_average()
                    delta_temp = temp - last_temp
                    tempRate = delta_temp / delta_time
                    if elapsed_time < cti:
                        #TODO controllo raffreddamento come ricottura
                        progress = min(elapsed_time / cti, 1.0)
                        print_status("Raffreddamento", elapsed_time, temp, progress)
                    else:
                        print_status("Rafreddamento", elapsed_time, temp, 1.0)
                        self.ctx.ssr_res.LOW()
                        print(f"Raffreddamento completato in {time_convert_str(elapsed_time)}.\n\n")
                        steps["cooling"] = True
                    last_time = elapsed_time
                    last_temp = temp
                    self.ctx.sq.add_sample("cooling", cti, temp, elapsed_time, temp_rate, self.ctx.ssr_res.get_state(), self.ctx.ssr_fan.get_state(), sys_temp)
                    
            process_time = time.time() - start_time
            self.ctx.ssr_res.LOW()
            self.ctx.ssr_fan.LOW()
            self.ctx.sq.process_complete(process_time, "OK")
            self.ctx.sq.log_samples()
            clear_values(self.params)
            input(f"{ANSI.BOLD}{ANSI.GREEN}Processo completato in {time_convert_str(process_time)}.\nPremere un tasto per continuare...{ANSI.RESET}")
            return "MAIN_MENU"
        
        except KeyboardInterrupt:
            process_time = time.time() - start_time
            self.ctx.ssr_res.LOW()
            self.ctx.ssr_fan.LOW()
            self.ctx.sq.process_complete(process_time, "USER_STOP")
            self.ctx.sq.log_samples()
            clear_values(self.params)
            input(f"\n{ANSI.BOLD}{ANSI.RED}Processo terminato dall'utente.\nPremere un tasto per continuare...{ANSI.RESET}")
            return "MAIN_MENU"
        
        except ErroreTimeout as e:
            process_time = time.time() - start_time
            self.ctx.ssr_res.LOW()
            self.ctx.ssr_fan.LOW()
            self.ctx.sq.process_complete(process_time, "TIMEOUT_ERROR")
            self.ctx.sq.log_samples()
            clear_values(self.params)
            print(f"{ANSI.BOLD}{ANSI.RED}ERRORE: Timeout nella fase {e.step}.\nTempo trascorso: {time_convert_str(e.elapsed, ms=True)}")
            print(f"- Il forno non ha raggiunto la temperatura target nel tempo massimo di {time_convert_str(e.max_time)}{ANSI.RESET}")
            input("Premere un tasto per continuare...")
            return "MAIN_MENU"

        except ErroreTemperatura as e:
            process_time = time.time() - start_time
            self.ctx.ssr_res.LOW()
            self.ctx.ssr_fan.LOW()
            self.ctx.sq.process_complete(process_time, "TEMP_ERROR")
            self.ctx.sq.log_samples()
            clear_values(self.params)
            print(f"{ANSI.BOLD}{ANSI.RED}ERRORE: Temperatura non stabile nella fase {e.step}.\nTempo trascorso: {time_convert_str(e.elapsed, ms=True)}")
            print(f"- La temperatura rilevata eccede il 10% di tolleranza.\nRilevata: {e.temp:.2f}°C - Target: {e.target:.2f}°C{ANSI.RESET}")
            input("Premere un tasto per continuare...")
            return "MAIN_MENU"
        
        except ErroreSonda as e:
            self.ctx.ssr_res.LOW()
            self.ctx.ssr_fan.LOW()
            clear_values(self.params)
            return "MAIN_MENU"