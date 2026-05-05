import os, time, json, sys
from consoleMenu import TextMenu, ANSI
from functools import partial
from datetime import datetime

def clearValues(params):
    try:
        for key,val in params.items():
            params[key] = None
    except:
        input("Errore cancellando i dati...")

def timeConvertStr(timesec, ms=False):
    parts = []
    if timesec is None:
        return None
    elif timesec >= 60 and timesec < 3600:
        sec = timesec % 60
        min = (timesec - sec)/60
        hr = 0
    elif timesec >= 3600:
        sec = timesec % 60
        min = ((timesec - sec) / 60) % 60 
        hr = (timesec - min - sec)/3600
    else:
        sec = timesec
        min = 0
        hr = 0
    if hr>0:
        parts.append(f"{hr:.0f} [h]")
    if min>0:
        parts.append(f"{min:.0f} [m]")
    if sec>0 and ms == False:
        parts.append(f"{sec:.0f} [s]")
    if sec>0 and ms == True:
        parts.append(f"{sec:.3f} [s]")
    return " ".join(parts)
        
def loadPresets(self, presetFile, menu):
    file = presetFile
    fileName = os.path.join("presets", file)
    with open(fileName) as fn:
        presets = json.load(fn)            
    for item in presets["values"]:
        if item is presets["values"][-1]:
            menu.add_option(item["id"], item["name"]+"\n", partial(self.setValueFromPreset, item))
        else:
            menu.add_option(item["id"], item["name"], partial(self.setValueFromPreset, item))
        
def completo(obj):
    return all(v is not None for v in obj.params.values())

def printStatus(step, elapsed, temp, progress):
    sys.stdout.write("\033[F\033[K")
    sys.stdout.write("\033[F\033[K")
    sys.stdout.write("\033[F\033[K")

    print(f"{step} in corso... Temperatura attuale: {temp:.2f} °C")
    print(f"Tempo trascorso: {timeConvertStr(elapsed, ms=True)}")

    lunghezzaBarra = 40
    percentBarra = int(lunghezzaBarra * progress)
    barra = "O" * percentBarra + "." * (lunghezzaBarra - percentBarra)
    textVal = int(progress*100)
    print(f"[{barra}] {textVal}%")

def todoPlaceh():
    input("\nNon ancora supportato. Premere qualunque tasto per continuare...\n")



class Essicatura:
    def __init__(self,ctx):
        self.params = {
            "target_temp": None,
            "heat_time": None
        }
        self.ctx = ctx
        self.MAXTIME = 15 #secondi massimi per il cambio temperatura, per debug
        self.textMenu = TextMenu("Essicatura", color_title=ANSI.MAGENTA, color_option=ANSI.CYAN)
        self.presetMenu = TextMenu("Preset Essicatura", color_title=ANSI.CYAN, color_option=ANSI.WHITE)
        self.textMenu.add_option("P", "Presets di Essicatura\n",self.presetMenu)
        self.textMenu.add_option("1", lambda: f"Imposta Target Temp.: {self.params['target_temp'] or '-'} [°C]", partial(self.setValue, "target_temp", "Target temperatura [°C]: "))
        self.textMenu.add_option("2", lambda: f"Imposta Durata      : {timeConvertStr(self.params['heat_time']) or '- [s]'}", partial(self.setValue,"heat_time","Durata essicatura [s]: "))
        self.textMenu.add_option("A", "Avvia", self.run, disabled=True, executable=True)
        #TODO se esiste file preset carica
        loadPresets(self,"essicatura.json",self.presetMenu)
        self.presetMenu.add_option("C", "Crea preset ", todoPlaceh)
     
         
    def setValue(self, value, message):
        try:
            v = float(input(message))
            self.params[value] = v
            if completo(self):
                self.textMenu.enableExec()
        except:
            print("Valore non valido.")
            input("Invio per continuare...")
    
    
    def setValueFromPreset(self, item):
        self.params["target_temp"] = item["target_temp"]
        self.params["heat_time"] = item["heat_time"]
        if completo(self):
            self.textMenu.enableExec()
        print("Preset caricato...")
        time.sleep(1)
        return "BACK"
        
    
    def run(self):
        #TODO completare logica
        process = "Essicatura"
        steps = {"heating":False, "dehydrating": False}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        t = self.params["target_temp"]
        ti = self.params["heat_time"]
        elapsedTime = 0
        lastTime = 0
        
        self.ctx.sq.addProcess(timestamp, process)
        try:
            print("Press CTRL+C to exit")
            startTime = heatStartTime = time.time()
            lastTemp = self.ctx.tc.readTempC_average()
            print("Inizio fase riscaldamento...\n\n\n")
            while not steps["heating"]:
                elapsedTime = time.time() - heatStartTime
                deltaTime = elapsedTime - lastTime
                if deltaTime > self.ctx.tc.interval:
                    systemp = 0 #TODO add dht
                    temp = self.ctx.tc.readTempC_average()
                    deltaTemp = temp - lastTemp
                    tempRate = deltaTemp/deltaTime
                    if temp < t and elapsedTime < self.MAXTIME:
                        self.ctx.ssr_res.HIGH()
                        #print(f"Heating... Tempo trascorso: {timeConvertStr(elapsedTime, ms=True)}")
                        progress = min(temp / t, 1.0)
                        printStatus("Riscaldamento", elapsedTime, temp, progress)
                        #TODO aggiungere il safetyoff se maxtime è superato, al momento off per debug
                    else:
                        self.ctx.ssr_res.LOW()
                        print(f"Riscaldamento completato in {timeConvertStr(elapsedTime)}.")
                        steps["heating"] = True
                    lastTime = elapsedTime
                    lastTemp = temp
                    self.ctx.sq.addSample("heating", t, temp, elapsedTime, tempRate, self.ctx.ssr_res.getState(), self.ctx.ssr_fan.getState(),systemp)
                    
            dehydrStartTime = time.time()
            elapsedTime = 0
            lastTime = 0
            lastTemp = self.ctx.tc.readTempC_average()
            print("Inizio fase essicazione...\n\n\n")
            while not steps["dehydrating"]:
                elapsedTime = time.time() - dehydrStartTime
                deltaTime = elapsedTime - lastTime
                if deltaTime > self.ctx.tc.interval:
                    systemp = 0 #TODO add dht
                    temp = self.ctx.tc.readTempC_average()
                    deltaTemp = temp - lastTemp
                    tempRate = deltaTemp/deltaTime
                    if temp < t:
                        self.ctx.ssr_res.HIGH()
                    else:
                        self.ctx.ssr_res.LOW()
                    if elapsedTime < ti:
                        #print(f"Essicazione... Tempo trascorso: {timeConvertStr(elapsedTime, ms=True)}")
                        progress = min(elapsedTime / ti, 1.0)
                        printStatus("Essicatura", elapsedTime, temp, progress)
                    else:
                        print(f"Essicazione completata in {timeConvertStr(elapsedTime)}.")
                        steps["dehydrating"] = True
                    lastTime = elapsedTime
                    lastTemp = temp
                    self.ctx.sq.addSample("soaking", t, temp, elapsedTime, tempRate, self.ctx.ssr_res.getState(), self.ctx.ssr_fan.getState(), systemp)
            
            processTime = time.time() - startTime
            input(f"Processo completato in {timeConvertStr(processTime)}. Premere un tasto per continuare...")    
            self.ctx.ssr_res.LOW()
            self.ctx.ssr_fan.LOW()
            self.ctx.sq.processComplete(processTime, "OK")
            self.ctx.sq.logSamples()
            clearValues(self.params)
            return "MAIN_MENU"
                
        except KeyboardInterrupt:
            print("\nProcesso terminato.")
            self.ctx.ssr_res.LOW()
            self.ctx.ssr_fan.LOW()
            self.ctx.sq.processComplete(processTime, "ERROR")
            self.ctx.sq.logSamples()
            clearValues(self.params)
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
        self.MAXTIME = 15 #secondi massimi per il cambio temperatura, per debug
        self.textMenu = TextMenu("Ricottura", color_title=ANSI.MAGENTA, color_option=ANSI.CYAN)
        self.presetMenu = TextMenu("Preset Ricottura", color_title=ANSI.CYAN, color_option=ANSI.WHITE)
        self.textMenu.add_option("P", "Presets di Ricottura\n",self.presetMenu)
        self.textMenu.add_option("1", lambda: f"Imposta Target Temp.: {self.params['target_temp'] or '-'} [°C]", partial(self.setValue, "target_temp", "Target temperatura [°C]: "))
        self.textMenu.add_option("2", lambda: f"Imposta Heat Time   : {timeConvertStr(self.params['reheat_duration']) or '- [s]'}", partial(self.setValue, "reheat_duration", "Durata ricottura [s]: "))
        self.textMenu.add_option("3", lambda: f"Imposta Cooling Rate: {self.params['cooling_rate'] or '-'} [°C/s]\n    Cooling time        : {timeConvertStr(self.params['cooling_time_calc']) or '- [s]'}", partial(self.setValue, "cooling_rate","Rate raffreddamento [°C/s]: "))
        self.textMenu.add_option("A", "Avvia", self.run, disabled=True, executable=True)
        #TODO se esiste file preset carica
        loadPresets(self, "ricottura.json", self.presetMenu)
        self.presetMenu.add_option("C", "Crea preset ", todoPlaceh)
     
        
    def setValue(self, value, message):
        try:
            v = float(input(message))
            self.params[value] = v
            if self.params["cooling_rate"] and self.params["target_temp"]:
                self.params["cooling_time_calc"] = round((self.params["target_temp"] - 20) / self.params["cooling_rate"])
            if completo(self):
                self.textMenu.enableExec()
        except:
            print("Valore non valido.")
            print("Invio per continuare...")
    
    
    def setValueFromPreset(self, item):
        self.params["target_temp"] = item["target_temp"]
        self.params["reheat_duration"] = item["reheat_duration"]
        self.params["cooling_rate"] = item["cooling_rate"]
        if self.params["cooling_rate"] and self.params["target_temp"]:
            self.params["cooling_time_calc"] = round((self.params["target_temp"] - 20) / self.params["cooling_rate"])
        if completo(self):
            self.textMenu.enableExec()
        print("Preset caricato...")
        time.sleep(1)
        return "BACK"
        
    
    def run(self):
        #TODO logica
        process = "Ricottura"
        steps = {"heating":False, "soak": False, "cooling": False}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        t = self.params["target_temp"]
        ti = self.params["reheat_duration"]
        c = self.params["cooling_rate"]
        ci = self.params["cooling_time_calc"]
        elapsedTime = 0
        lastTime = 0
        
        self.ctx.sq.addProcess(timestamp, process)
        try:
            print("Press CTRL+C to exit")
            startTime = heatStartTime = time.time()
            lastTemp = self.ctx.tc.readTempC_average()
            print("Inizio fase riscaldamento...")
            while not steps["heating"]:
                elapsedTime = time.time() - heatStartTime
                deltaTime = elapsedTime - lastTime
                if deltaTime > self.ctx.tc.interval:
                    systemp = 0 #TODO add dht
                    temp = self.ctx.tc.readTempC_average()
                    deltaTemp = temp - lastTemp
                    tempRate = deltaTemp/deltaTime
                    if temp < t and elapsedTime < self.MAXTIME:
                        self.ctx.ssr_res.HIGH()
                        print(f"Heating... Tempo trascorso: {timeConvertStr(elapsedTime, ms=True)}...")
                        #TODO aggiungere il safetyoff se maxtime è superato, al momento off per debug
                    else:
                        self.ctx.ssr_res.LOW()
                        print(f"Riscaldamento completato in {timeConvertStr(elapsedTime)}.")
                        steps["heating"] = True
                    lastTime = elapsedTime
                    lastTemp = temp
                    self.ctx.sq.addSample("heating", t, temp, elapsedTime, tempRate, self.ctx.ssr_res.getState(), self.ctx.ssr_fan.getState(), systemp)
                
            soakStartTime = time.time()
            elapsedTime = 0
            lastTime = 0
            lastTemp = self.ctx.tc.readTempC_average()
            print("Inizio fase mantenimento temperatura...")
            while not steps["soak"]:
                elapsedTime = time.time() - soakStartTime
                deltaTime = elapsedTime - lastTime
                if deltaTime > self.ctx.tc.interval:
                    systemp = 0 #TODO add dht
                    temp = self.ctx.tc.readTempC_average()
                    deltaTemp = temp - lastTemp
                    tempRate = deltaTemp/deltaTime
                    if temp < t:
                        self.ctx.ssr_res.HIGH()
                    else:
                        self.ctx.ssr_res.LOW()
                    if elapsedTime < ti:
                        print(f"Soaking... Tempo trascorso: {timeConvertStr(elapsedTime, ms=True)}...")
                    else:
                        print(f"Soaking completato in {timeConvertStr(elapsedTime)}.")
                        steps["soak"] = True
                    lastTime = elapsedTime
                    lastTemp = temp
                    self.ctx.sq.addSample("soaking", t, temp, elapsedTime, tempRate, self.ctx.ssr_res.getState(), self.ctx.ssr_fan.getState(), systemp)
                
            coolStartTime = time.time()
            elapsedTime = 0
            lastTime = 0
            lastTemp = self.ctx.tc.readTempC_average()
            print("Inizio fase raffreddamento...")
            while not steps["cooling"]:
                elapsedTime = time.time() - coolStartTime
                deltaTime = elapsedTime - lastTime
                if deltaTime > self.ctx.tc.interval:
                    systemp = 0 #TODO adddht
                    temp = self.ctx.tc.readTempC_average()
                    deltaTemp = temp - lastTemp
                    tempRate = deltaTemp/deltaTime
                    if elapsedTime < ci:
                        print(f"Cooling... Tempo trascorso: {timeConvertStr(elapsedTime, ms=True)}...")
                    else:
                        print(f"Cooling completato in {timeConvertStr(elapsedTime)}.")
                        steps["cooling"] = True
                    lastTime = elapsedTime
                    lastTemp = temp
                    self.ctx.sq.addSample("cooling", t, temp, elapsedTime, tempRate, self.ctx.ssr_res.getState(), self.ctx.ssr_fan.getState(), systemp)
                    
            processTime = time.time() - startTime
            input(f"Processo completato in {timeConvertStr(processTime)}.\nPremere un tasto per continuare...")
            self.ctx.ssr_res.LOW()
            self.ctx.ssr_fan.LOW()
            self.ctx.sq.processComplete(processTime, "OK")
            self.ctx.sq.logSamples()
            clearValues(self.params)
            return "MAIN_MENU"
        
        except KeyboardInterrupt:
            print("\nProcesso terminato.")
            self.ctx.ssr_res.LOW()
            self.ctx.ssr_fan.LOW()
            self.ctx.sq.processComplete(processTime, "ERROR")
            self.ctx.sq.logSamples()
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
        self.presetMenu = TextMenu("Preset Saldatura SMD", color_title=ANSI.CYAN, color_option=ANSI.WHITE)
        self.textMenu.add_option("P", "Presets di Saldatura SMD\n",self.presetMenu)
        self.textMenu.add_option("1", lambda: f"Imposta Pre-Heat temp   : {self.params['ph_temp'] or '-'} [°C]", partial(self.setValue,"ph_temp","Target temperatura [°C]: "))
        self.textMenu.add_option("2", lambda: f"Imposta Pre-Heat rate   : {self.params['ph_rate'] or '-'} [°C/s]\n    Pre-Heat time           : {timeConvertStr(self.params['ph_time_calc']) or '- [s]'}", partial(self.setValue,"ph_rate","Target rate [°C/s]: "))
        self.textMenu.add_option("3", lambda: f"Imposta Soak time       : {timeConvertStr(self.params['soak_time']) or '- [s]'}", partial(self.setValue,"soak_time","Tempo soak [s]: "))
        self.textMenu.add_option("4", lambda: f"Imposta Reflow temp     : {self.params['reflow_temp'] or '-'} [°C]", partial(self.setValue,"reflow_temp","Target temperatura [°C]: "))
        self.textMenu.add_option("5", lambda: f"Imposta Reflow rate     : {self.params['reflow_rate'] or '-'} [°C/s]\n    Reflow time             : {timeConvertStr(self.params['reflow_time_calc']) or '- [s]'}", partial(self.setValue,"reflow_rate","Target rate [°C/s]: "))
        self.textMenu.add_option("6", lambda: f"Imposta Reflow peak time: {timeConvertStr(self.params['reflow_peak_time']) or '- [s]'}", partial(self.setValue,"reflow_peak_time","Tempo peak [°C]: "))
        self.textMenu.add_option("7", lambda: f"Imposta Cooling rate    : {self.params['cooling_rate'] or '-'} [°C/s]\n    Cooling time            : {timeConvertStr(self.params['cooling_time_calc']) or '- [s]'}", partial(self.setValue,"cooling_rate","Target rate [s]: "))
        self.textMenu.add_option("A", "Avvia", self.run, disabled=True, executable=True)
        #TODO se esiste file preset carica
        loadPresets(self, "saldatura.json", self.presetMenu)
        self.presetMenu.add_option("C", "Crea preset ", todoPlaceh)
     
        
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

            if completo(self):
                self.textMenu.enableExec()
        except:
            print("Valore non valido.")
            print("Invio per continuare...")
    
    
    def setValueFromPreset(self, item):
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

        if completo(self):
            self.textMenu.enableExec()
        print("Preset caricato...")
        time.sleep(1)
        return "BACK"
        
    
    def run(self):
        #TODO manca logica
        
        print("Saldatura eseguita / placeholder")
        time.sleep(2)
        clearValues(self.params)
        return "MAIN_MENU"