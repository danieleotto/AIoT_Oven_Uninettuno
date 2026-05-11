import os, time, json, sys
from console_menu import TextMenu, ANSI
from functools import partial
from customlib.functions import todo_placeholder, get_timestamp, time_convert_str, clear_console
from customlib.custom_exceptions import ErroreTimeout, ErroreTemperatura, ErroreSonda
from customlib.custom_classes import Context, Heating, Soaking, Cooling


def clear_values(params:dict, menu:TextMenu) -> None:
    try:
        for key,val in params.items():
            params[key] = None
        menu.disable_exec()
        print("Parametri cancellati...")
        time.sleep(0.5)
    except:
        input("Errore durante il cancellamento dei dati.\nPremere un tasto per continuare...")
    
        
def load_presets(self, preset_file:str, menu:TextMenu) -> None:
    #TODO presetFile type
    #file = preset_file
    filename = os.path.join("presets", preset_file)
    with open(filename) as fn:
        presets = json.load(fn)            
    for item in presets["values"]:
        if item is presets["values"][-1]:
            menu.add_option(item["id"], item["name"]+"\n", partial(self._set_value_from_preset, item))
        else:
            menu.add_option(item["id"], item["name"], partial(self._set_value_from_preset, item))
    #TODO verificare il preset creators
    menu.add_option("C", "Crea preset ", todo_placeholder)
  
  
def is_complete(obj:dict) -> bool:
    return all(v is not None for v in obj.values())


def print_title(title:str) -> None:
    print("\n"+"="*50)
    print(f"{ANSI.BOLD}{ANSI.MAGENTA}{title}{ANSI.RESET}")
    print("="*50)



    
class Essicatura:
    """Gestisce il processo di essicatura."""
    def __init__(self, ctx:Context) -> None:
        self.ctx = ctx
        self.process_name = "Essicatura"
        self.params:dict[str, float | None] = {
            "ris_target_temp": None,
            "ess_target_time": None
        }
        self.process_menu = TextMenu("                --- ESSICATURA ---", color_title=ANSI.MAGENTA, color_option=ANSI.CYAN)
        self.preset_menu = TextMenu("            --- PRESET ESSICATURA ---", color_title=ANSI.CYAN, color_option=ANSI.WHITE)
        self.process_menu.add_option("P", "Presets di Essicatura", self.preset_menu)
        self.process_menu.add_option("D", "Cancella dati inseriti\n", partial(clear_values, self.params, self.process_menu))
        self.process_menu.add_option("1", 
                                     lambda: f"Imposta Target Temp.: {self.params['ris_target_temp'] or '-'} [°C]", 
                                     partial(self._set_value, "ris_target_temp", "Target temperatura [°C]: "))
        self.process_menu.add_option("2", 
                                     lambda: f"Imposta Durata      : {time_convert_str(self.params['ess_target_time']) or '- [s]'}", 
                                     partial(self._set_value,"ess_target_time","Durata essicatura [s]: "))
        self.process_menu.add_option("A", "Avvia", self.run, disabled=True, executable=True)
        #TODO se esiste file preset carica
        load_presets(self,"essicatura.json",self.preset_menu)     
     

    def _set_value(self, key:str, message:str) -> None:
        try:
            v = float(input(message))
            self.params[key] = v
            if is_complete(self.params):
                self.process_menu.enable_exec()
        except ValueError:
            print("Valore non valido.")
            input("Invio per continuare...")
    
    
    def _set_value_from_preset(self, value):
        self.params["ris_target_temp"] = value["ris_target_temp"]
        self.params["ess_target_time"] = value["ess_target_time"]
        if is_complete(self.params):
            self.process_menu.enable_exec()
        print("Preset caricato...")
        time.sleep(0.5)
        return "BACK"
        
    
    def run(self) -> str:
        timestamp = get_timestamp(readable=False)
        self.ctx.sq.add_process(timestamp, self.process_name)
        start_time:float = time.time()
        
        riscaldamento = Heating("Riscaldamento", self.ctx, self.params['ris_target_temp'], None, None)
        essicatura = Soaking("Essicatura", self.ctx, self.params['ris_target_temp'], self.params['ess_target_time'])

        try:
            clear_console()    
            print_title(self.process_menu.title)
            print("Press CTRL+C per interrompere il processo.\n")
            start_temp = self.ctx.tc.controllo_sonda(self.ctx.sampling_interval)
            
            riscaldamento.run()
            essicatura.run()
                    
            process_time = time.time() - start_time
            self.ctx.sq.process_complete(process_time, "OK")
            input(f"{ANSI.BOLD}{ANSI.GREEN}Processo completato in {time_convert_str(process_time)}.\nPremere un tasto per continuare...{ANSI.RESET}\n")    
            return "MAIN_MENU"
                
        except KeyboardInterrupt:
            process_time = time.time() - start_time
            self.ctx.sq.process_complete(process_time, "USER_STOP")
            input(f"\n{ANSI.BOLD}{ANSI.RED}Processo terminato dall'utente.\nPremere un tasto per continuare...{ANSI.RESET}")
            return "MAIN_MENU"

        except ErroreTimeout as e:
            process_time = time.time() - start_time
            self.ctx.sq.process_complete(process_time, "TIMEOUT_ERROR")
            print(f"{ANSI.BOLD}{ANSI.RED}ERRORE: Timeout nella fase {e.step}.\nTempo trascorso: {time_convert_str(e.elapsed, ms=True)}")
            print(f"- Il forno non ha raggiunto la temperatura target nel tempo massimo di {time_convert_str(e.max_time)}{ANSI.RESET}")
            input("Premere un tasto per continuare...")
            return "MAIN_MENU"

        except ErroreTemperatura as e:
            process_time = time.time() - start_time
            self.ctx.sq.process_complete(process_time, "TEMP_ERROR")
            print(f"{ANSI.BOLD}{ANSI.RED}ERRORE: Temperatura non stabile nella fase {e.step}.\nTempo trascorso: {time_convert_str(e.elapsed, ms=True)}")
            print(f"- La temperatura rilevata eccede il 10% di tolleranza.\nRilevata: {e.temp:.2f}°C - Target: {e.target:.2f}°C{ANSI.RESET}")
            input("Premere un tasto per continuare...")
            return "MAIN_MENU"
        
        except ErroreSonda:
            print(f"{ANSI.BOLD}{ANSI.RED}ERRORE: Sonda non rilevata.{ANSI.RESET}")
            input("Premere un tasto per continuare...")
            return "MAIN_MENU"

        finally:
            self.ctx.ssr_res.turn_off()
            self.ctx.ssr_fan.turn_off()
            self.ctx.sq.log_samples()




class Ricottura:
    """Gestisce il processo di ricottura."""
    def __init__(self, ctx:Context) -> None:
        self.ctx = ctx
        self.process_name = "Ricottura"
        self.params:dict[str, float | None] = {
            "ris_target_temp": None,
            "ric_target_time": None,
            "cool_target_temp_rate": None,
            "cool_target_time_calc": None
        }
        self.process_menu = TextMenu("                 --- RICOTTURA ---", color_title=ANSI.MAGENTA, color_option=ANSI.CYAN)
        self.preset_menu = TextMenu("             --- PRESET RICOTTURA ---", color_title=ANSI.CYAN, color_option=ANSI.WHITE)
        self.process_menu.add_option("P", "Presets di Ricottura\n",self.preset_menu)
        self.process_menu.add_option("1", 
                                     lambda: f"Imposta Target Temp.: {self.params['ris_target_temp'] or '-'} [°C]", 
                                     partial(self._set_value, "ris_target_temp", "Target temperatura [°C]: "))
        self.process_menu.add_option("2", 
                                     lambda: f"Imposta Heat Time   : {time_convert_str(self.params['ric_target_time']) or '- [s]'}", 
                                     partial(self._set_value, "ric_target_time", "Durata ricottura [s]: "))
        self.process_menu.add_option("3", 
                                     lambda: f"Imposta Cooling Rate: {self.params['cool_target_temp_rate'] or '-'} [°C/s]\n    Cooling time        : {time_convert_str(self.params['cool_target_time_calc']) or '- [s]'}", 
                                     partial(self._set_value, "cool_target_temp_rate","Rate raffreddamento [°C/s]: "))
        self.process_menu.add_option("A", "Avvia", self.run, disabled=True, executable=True)
        #TODO se esiste file preset carica
        load_presets(self, "ricottura.json", self.preset_menu)
     
        
    def _set_value(self, value, message):
        try:
            v = float(input(message))
            self.params[value] = v
            if self.params["cool_target_temp_rate"] and self.params["ris_target_temp"]:
                self.params["cool_target_time_calc"] = round((self.params["ris_target_temp"] - 20) / self.params["cool_target_temp_rate"])
            if is_complete(self.params):
                self.process_menu.enable_exec()
        except ValueError:
            print("Valore non valido.")
            print("Invio per continuare...")
    
    
    def _set_value_from_preset(self, item):
        self.params["ris_target_temp"] = item["ris_target_temp"]
        self.params["ric_target_time"] = item["ric_target_time"]
        self.params["cool_target_temp_rate"] = item["cool_target_temp_rate"]
        if self.params["cool_target_temp_rate"] and self.params["ris_target_temp"]:
            self.params["cool_target_time_calc"] = round((self.params["ris_target_temp"] - 20) / self.params["cool_target_temp_rate"])
        if is_complete(self.params):
            self.process_menu.enable_exec()
        print("Preset caricato...")
        time.sleep(0.5)
        return "BACK"
        
    
    def run(self) -> str:
        timestamp = get_timestamp(readable=False)
        self.ctx.sq.add_process(timestamp, self.process_name)
        start_time:float = time.time()
        
        
        riscaldamento = Heating("Riscaldamento", self.ctx, self.params['ris_target_temp'], None, None)
        ricottura = Soaking("Ricottura", self.ctx, self.params['ris_target_temp'], self.params['ric_target_time'], None)
        raffreddamento = Cooling("Raffreddamento", self.ctx, None, self.params['cool_target_time_calc'], self.params['cool_target_temp_rate'])
                
        try:
            clear_console()
            print_title(self.process_menu.title)
            print("Premi CTRL+C per interrompere il processo.\n")
            start_temp = self.ctx.tc.controllo_sonda(self.ctx.sampling_interval)
            raffreddamento.target_temp = start_temp + 20 #messo qui per poter essere intercettato dal try
            
            riscaldamento.run()
            ricottura.run()
            raffreddamento.run()               
                    
            process_time = time.time() - start_time
            self.ctx.sq.process_complete(process_time, "OK")
            input(f"{ANSI.BOLD}{ANSI.GREEN}Processo completato in {time_convert_str(process_time)}.\nPremere un tasto per continuare...{ANSI.RESET}")
            return "MAIN_MENU"
        
        except KeyboardInterrupt:
            process_time = time.time() - start_time
            self.ctx.sq.process_complete(process_time, "USER_STOP")
            input(f"\n{ANSI.BOLD}{ANSI.RED}Processo terminato dall'utente.\nPremere un tasto per continuare...{ANSI.RESET}")
            return "MAIN_MENU"

        except ErroreTimeout as e:
            process_time = time.time() - start_time
            self.ctx.sq.process_complete(process_time, "TIMEOUT_ERROR")
            print(f"{ANSI.BOLD}{ANSI.RED}ERRORE: Timeout nella fase {e.step}.\nTempo trascorso: {time_convert_str(e.elapsed, ms=True)}")
            print(f"- Il forno non ha raggiunto la temperatura target nel tempo massimo di {time_convert_str(e.max_time)}{ANSI.RESET}")
            input("Premere un tasto per continuare...")
            return "MAIN_MENU"

        except ErroreTemperatura as e:
            process_time = time.time() - start_time
            self.ctx.sq.process_complete(process_time, "TEMP_ERROR")
            print(f"{ANSI.BOLD}{ANSI.RED}ERRORE: Temperatura non stabile nella fase {e.step}.\nTempo trascorso: {time_convert_str(e.elapsed, ms=True)}")
            print(f"- La temperatura rilevata eccede il 10% di tolleranza.\nRilevata: {e.temp:.2f}°C - Target: {e.target:.2f}°C{ANSI.RESET}")
            input("Premere un tasto per continuare...")
            return "MAIN_MENU"
        
        except ErroreSonda:
            print(f"{ANSI.BOLD}{ANSI.RED}ERRORE: Sonda non rilevata.{ANSI.RESET}")
            input("Premere un tasto per continuare...")
            return "MAIN_MENU"
        
        finally:
            self.ctx.ssr_res.turn_off()
            self.ctx.ssr_fan.turn_off()
            self.ctx.sq.log_samples()




class SaldaturaSMD:
    """Gestisce il processo di saldatura SMD per reflow."""
    def __init__(self, ctx:Context) -> None:
        self.ctx = ctx
        self.process_name = "Saldatura"
        self.params:dict[str, float | None] = {
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
        self.process_menu = TextMenu("              --- SALDATURA SMD ---", color_title=ANSI.MAGENTA, color_option=ANSI.CYAN)
        self.preset_menu = TextMenu("           --- PRESET SALDATURA SMD ---", color_title=ANSI.CYAN, color_option=ANSI.WHITE)
        self.process_menu.add_option("P", "Presets di Saldatura SMD\n",self.preset_menu)
        self.process_menu.add_option("1", 
                                     lambda: f"Imposta Pre-Heat temp   : {self.params['ph_temp'] or '-'} [°C]", 
                                     partial(self._set_value,"ph_temp","Target temperatura [°C]: "))
        self.process_menu.add_option("2", 
                                     lambda: f"Imposta Pre-Heat rate   : {self.params['ph_rate'] or '-'} [°C/s]\n    Pre-Heat time           : {time_convert_str(self.params['ph_time_calc']) or '- [s]'}", 
                                     partial(self._set_value,"ph_rate","Target rate [°C/s]: "))
        self.process_menu.add_option("3", 
                                     lambda: f"Imposta Soak time       : {time_convert_str(self.params['soak_time']) or '- [s]'}", 
                                     partial(self._set_value,"soak_time","Tempo soak [s]: "))
        self.process_menu.add_option("4", 
                                     lambda: f"Imposta Reflow temp     : {self.params['reflow_temp'] or '-'} [°C]", 
                                     partial(self._set_value,"reflow_temp","Target temperatura [°C]: "))
        self.process_menu.add_option("5", 
                                     lambda: f"Imposta Reflow rate     : {self.params['reflow_rate'] or '-'} [°C/s]\n    Reflow time             : {time_convert_str(self.params['reflow_time_calc']) or '- [s]'}", 
                                     partial(self._set_value,"reflow_rate","Target rate [°C/s]: "))
        self.process_menu.add_option("6", 
                                     lambda: f"Imposta Reflow peak time: {time_convert_str(self.params['reflow_peak_time']) or '- [s]'}", 
                                     partial(self._set_value,"reflow_peak_time","Tempo peak [°C]: "))
        self.process_menu.add_option("7", 
                                     lambda: f"Imposta Cooling rate    : {self.params['cooling_rate'] or '-'} [°C/s]\n    Cooling time            : {time_convert_str(self.params['cooling_time_calc']) or '- [s]'}", 
                                     partial(self._set_value,"cooling_rate","Target rate [s]: "))
        self.process_menu.add_option("A", "Avvia", self.run, disabled=True, executable=True)
        #TODO se esiste file preset carica
        load_presets(self, "saldatura.json", self.preset_menu)
     
        
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

            if is_complete(self.params):
                self.process_menu.enable_exec()
        except ValueError:
            print("Valore non valido.")
            print("Invio per continuare...")
    
    
    def _set_value_from_preset(self, item):
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

        if is_complete(self.params):
            self.process_menu.enable_exec()
        print("Preset caricato...")
        time.sleep(0.5)
        return "BACK"
        
    
    def run(self) -> str:
        timestamp = get_timestamp(readable=False)
        self.ctx.sq.add_process(timestamp, self.process_name)
        start_time:float = time.time()
        
        preheat = Heating("Pre-heating", self.ctx, self.params['ph_temp'], self.params['ph_time_calc'], self.params['ph_rate'])
        soaking = Soaking("Soaking", self.ctx, self.params['soak_temp_calc'], self.params['soak_time'])
        reflow = Heating("Reflow", self.ctx, self.params['reflow_temp'], self.params['reflow_time_calc'], self.params['reflow_rate'])
        reflow_peak = Soaking("Reflow Peak Heat", self.ctx, self.params['reflow_temp'], self.params['reflow_peak_time'])
        cooling= Cooling("Cooling", self.ctx, None, self.params['cooling_time_calc'], self.params['cooling_rate'])
        
        
        try:
            clear_console()
            print_title(self.process_menu.title)
            print("Premi CTRL+C per interrompere il processo.\n")
            start_temp = self.ctx.tc.controllo_sonda(self.ctx.sampling_interval)
            cooling.target_time = start_temp + 20 #TODO vedi commento su ricottura
            
            preheat.run()
            soaking.run()
            reflow.run()
            reflow_peak.run()
            cooling.run()
                                
            process_time = time.time() - start_time
            self.ctx.sq.process_complete(process_time, "OK")
            input(f"{ANSI.BOLD}{ANSI.GREEN}Processo completato in {time_convert_str(process_time)}.\nPremere un tasto per continuare...{ANSI.RESET}")
            return "MAIN_MENU"
        
        except KeyboardInterrupt:
            process_time = time.time() - start_time
            self.ctx.sq.process_complete(process_time, "USER_STOP")
            input(f"\n{ANSI.BOLD}{ANSI.RED}Processo terminato dall'utente.\nPremere un tasto per continuare...{ANSI.RESET}")
            return "MAIN_MENU"
        
        except ErroreTimeout as e:
            process_time = time.time() - start_time
            self.ctx.sq.process_complete(process_time, "TIMEOUT_ERROR")
            print(f"{ANSI.BOLD}{ANSI.RED}ERRORE: Timeout nella fase {e.step}.\nTempo trascorso: {time_convert_str(e.elapsed, ms=True)}")
            print(f"- Il forno non ha raggiunto la temperatura target nel tempo massimo di {time_convert_str(e.max_time)}{ANSI.RESET}")
            input("Premere un tasto per continuare...")
            return "MAIN_MENU"

        except ErroreTemperatura as e:
            process_time = time.time() - start_time
            self.ctx.sq.process_complete(process_time, "TEMP_ERROR")
            print(f"{ANSI.BOLD}{ANSI.RED}ERRORE: Temperatura non stabile nella fase {e.step}.\nTempo trascorso: {time_convert_str(e.elapsed, ms=True)}")
            print(f"- La temperatura rilevata eccede il 10% di tolleranza.\nRilevata: {e.temp:.2f}°C - Target: {e.target:.2f}°C{ANSI.RESET}")
            input("Premere un tasto per continuare...")
            return "MAIN_MENU"
        
        except ErroreSonda:
            return "MAIN_MENU"
        
        finally:
            self.ctx.ssr_res.turn_off()
            self.ctx.ssr_fan.turn_off()
            self.ctx.sq.log_samples()