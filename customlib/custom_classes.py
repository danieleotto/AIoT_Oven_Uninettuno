import os, json, sys
from functools import partial
from thermocouple import Termocoppia
from sqlite_db import SQLiteDB
from ss_relay import SolidStateRelay
from temp_sensor import TempSensor
from console_menu import TextMenu, ANSI
from customlib.functions import time_convert_str
from customlib.custom_exceptions import ErroreSonda, ErroreTemperatura, ErroreTimeout



class Context:
    def __init__(
        self, 
        thermocouple:Termocoppia,
        sanpling_interval:float,
        database:SQLiteDB,
        ssr_resistance:SolidStateRelay,
        ssr_ovenfan:SolidStateRelay,
        dht22:TempSensor = None,
        pzem = None
    ) -> None:
        #TODO pzem sensor type
        self.tc = thermocouple
        self.sampling_interval = sanpling_interval
        self.sq = database
        self.ssr_res = ssr_resistance
        self.ssr_fan = ssr_ovenfan
        self.dht22 = dht22
        self.pzem = pzem
        
        
class Process:
    def print_title(title:str) -> None:
        print("\n"+"="*50)
        print(f"{ANSI.BOLD}{ANSI.MAGENTA}{title}{ANSI.RESET}")
        print("="*50)


    def clear_values(params:dict) -> None:
            for key,val in params.items():
                params[key] = None
            input("Errore cancellando i dati...")
        
            
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
    
            
    def is_complete(obj:dict) -> bool:
        #TODO types (considerare di fare una classe processi)
        return all(v is not None for v in obj.values())


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
