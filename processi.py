import os, time
from consoleMenu import TextMenu, ANSI
from functools import partial
from datetime import datetime

def clearValues(params):
    try:
        for key,val in params.items():
            params[key] = None
    except:
        input("Errore cancellando i dati...")
        

class Essicatura:
    def __init__(self,ctx):
        self.params = {
            "target_temp": None,
            "heat_time": None
        }
        self.ctx = ctx
        self.textMenu = TextMenu("Essicatura", color_title=ANSI.MAGENTA, color_option=ANSI.CYAN)
        #self.presetMenu = TextMenu("Preset Essicatura", color_title=ANSI.CYAN, color_option=ANSI.WHITE)
        #self.textMenu.add_option("0", "Scegli preset di Essicatura",self.presetMenu)
        self.textMenu.add_option("1", lambda: f"Imposta Target Temp.: {self.params['target_temp'] or '-'} [°C]", partial(self.setValue, "target_temp", "Target temperatura [°C]: "))
        self.textMenu.add_option("2", lambda: f"Imposta Durata      : {self.params['heat_time'] or '-'} [sec]", partial(self.setValue,"heat_time","Durata essicatura [sec]: "))
        self.textMenu.add_option("A", "Avvia", self.run, disabled=True, executable=True)
    
    def clear(self):
        os.system("clear" if os.name=="posix" else "cls")
        
    def completo(self):
        return all(v is not None for v in self.params.values())
    
    def setValue(self, value, message):
        try:
            v = float(input(message))
            self.params[value] = v
            if self.completo():
                self.textMenu.enableExec()
        except:
            print("Valore non valido.")
            print("Invio per continuare...")
    
    
    def run(self):
        process = "Essicatura"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        t = self.params["target_temp"]
        ti = self.params["heat_time"]
        elapsedTime = 0
        lastTime = 0
        deltaTime = 0
        lastTemp = 0
        deltaTemp = 0
        tempRate = 0
        self.ctx.sq.addProcess(timestamp, process)
        try:
            print("Press CTRL+C to exit")
            start_time = time.time()
            while elapsedTime < ti:
                #TODO logica reale
                
                avgTemp = self.ctx.tc.readTempC_average()
                
                if lastTemp != 0:
                    deltaTemp = avgTemp-lastTemp
                    deltaTime = elapsedTime-lastTime
                    tempRate = deltaTemp/deltaTime
                
                if avgTemp < t:
                    self.ctx.ssr_res.HIGH()
                else:
                    self.ctx.ssr_res.LOW()

                #sysTemp = dht22.getTemperature()
                sysTemp = 22.0
                idproc = self.ctx.sq.getLastId("listaprocessi")
                self.ctx.sq.addSample(idproc, t, avgTemp, elapsedTime, tempRate, self.ctx.ssr_res.getState(), self.ctx.ssr_fan.getState(), sysTemp)
                
                idsample = self.ctx.sq.getLastId("campioni")
                self.ctx.lg.log(f"{idproc},{process},{idsample},{t:.2f},{avgTemp:.2f},{elapsedTime:.2f},{tempRate:.2f},{self.ctx.ssr_res.getState()},{self.ctx.ssr_fan.getState()},{sysTemp:.2f}\n")
                print(f"Temp: {avgTemp:.2f}, time: {elapsedTime:.2f}, rate: {tempRate:.2f}, sample: {idsample}")
                
                time.sleep(self.ctx.tc.interval)
                
                lastTemp = avgTemp
                lastTime = elapsedTime
                elapsedTime = time.time() - start_time
            self.ctx.ssr_res.LOW()
            self.ctx.ssr_fan.LOW()
            clearValues(self.params)
            return "MAIN_MENU"
                

        except KeyboardInterrupt:
            print("\nProcesso terminato.")
            self.ctx.ssr_res.LOW()
            self.ctx.ssr_fan.LOW()
            return "MAIN_MENU"
        


class Ricottura:
    def __init__(self, ctx):
        self.params = {
            "target_temp": None,
            "reheat_duration": None,
            "cooling_rate": None,
            "cooling_time_calc": None
        }
        self.ctx = ctx
        self.textMenu = TextMenu("Ricottura", color_title=ANSI.MAGENTA, color_option=ANSI.CYAN)
        self.textMenu.add_option("1", lambda: f"Imposta Target Temp.: {self.params['target_temp'] or '-'} [°C]", partial(self.setValue, "target_temp", "Target temperatura [°C]: "))
        self.textMenu.add_option("2", lambda: f"Imposta Heat Time   : {self.params['reheat_duration'] or '-'} [sec]", partial(self.setValue, "reheat_duration", "Durata ricottura [sec]: "))
        self.textMenu.add_option("3", lambda: f"Imposta Cooling Rate: {self.params['cooling_rate'] or '-'} [°C/sec]\n    Cooling time   : {self.params["cooling_time_calc"] or '-'}", partial(self.setValue, "cooling_rate","Rate raffreddamento [°C/sec]: "))
        self.textMenu.add_option("A", "Avvia", self.run, disabled=True, executable=True)
    
    def clear(self):
        os.system("clear" if os.name=="posix" else "cls")
        
    def completo(self):
        return all(v is not None for v in self.params.values())
    
    def setValue(self, value, message):
        try:
            v = float(input(message))
            self.params[value] = v
            if self.params["cooling_rate"] and self.params["target_temp"]:
                self.params["cooling_time_calc"] = round((self.params["target_temp"] - 20) / self.params["cooling_rate"])
            if self.completo():
                self.textMenu.enableExec()
        except:
            print("Valore non valido.")
            print("Invio per continuare...")

    def run(self):
        #TODO logica
        
        print("Operazione terminata... ritorno al menu principale.")
        time.sleep(2)
        clearValues(self.params)
        return "MAIN_MENU"


class SaldaturaSMD:
    def __init__(self,ctx):
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
        self.textMenu = TextMenu("Saldatura SMD", color_title=ANSI.MAGENTA, color_option=ANSI.CYAN)
        self.textMenu.add_option("1", lambda: f"Imposta Pre-Heat time   : {self.params['ph_temp'] or '-'} [°C]", partial(self.setValue,"ph_temp","Target temperatura [°C]: "))
        self.textMenu.add_option("2", lambda: f"Imposta Pre-Heat rate   : {self.params['ph_rate'] or '-'} [°C/sec]\n    Pre-Heat time           : {self.params['ph_time_calc'] or '-'} [sec]", partial(self.setValue,"ph_rate","Target rate [°C/sec]: "))
        self.textMenu.add_option("3", lambda: f"Imposta Soak time       : {self.params['soak_time'] or '-'} [sec]", partial(self.setValue,"soak_time","Tempo soak [sec]: "))
        self.textMenu.add_option("4", lambda: f"Imposta Reflow temp     : {self.params['reflow_temp'] or '-'} [°C]", partial(self.setValue,"reflow_temp","Target temperatura [°C]: "))
        self.textMenu.add_option("5", lambda: f"Imposta Reflow rate     : {self.params['reflow_rate'] or '-'} [°C/sec]\n    Reflow time             : {self.params['reflow_time_calc'] or '-'} [sec]", partial(self.setValue,"reflow_rate","Target rate [°C/sec]: "))
        self.textMenu.add_option("6", lambda: f"Imposta Reflow peak time: {self.params['reflow_peak_time'] or '-'} [sec]", partial(self.setValue,"reflow_peak_time","Tempo peak [°C]: "))
        self.textMenu.add_option("7", lambda: f"Imposta Cooling rate    : {self.params['cooling_rate'] or '-'} [°C/sec]\n    Cooling time            : {self.params['cooling_time_calc'] or '-'} [sec]", partial(self.setValue,"cooling_rate","Target rate [sec]: "))
        self.textMenu.add_option("A", "Avvia", self.run, disabled=True, executable=True)

    def completo(self):
        return all(v is not None for v in self.params.values())
        
    def setValue(self, value, message):
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

            if self.completo():
                self.textMenu.enableExec()
        except:
            print("Valore non valido.")
            print("Invio per continuare...")

    def run(self):
        #TODO manca logica
        
        print("Saldatura eseguita / placeholder")
        time.sleep(2)
        clearValues(self.params)
        return "MAIN_MENU"