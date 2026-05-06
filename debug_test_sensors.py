from termocoppia import Termocoppia
from ssrelay import SolidStateRelay
from consoleMenu import TextMenu, ANSI
from functools import partial
from dht22 import DHT22
from PZEM004Tlib import PZEM004T
from PZEM004TModbuslib import PZEM004TModbus
import json, time

def tc_test(sampling):
    try:
        print("Test Termocoppia.\nCTRL+C per terminare.")
        if tc.inizializza(sampling_interval=sampling, debug=True) is not None:
            print("\n")
            while True:
                print(f"Buffer: {tc.buffer}  |  LastTemp: {t}  | LastAVG: {temp}")
                t = tc.readTC()
                temp = tc.readTempC_average()
                time.sleep(sampling)
        else:
            input("Sonda non rilevata, programma terminato.")
    except KeyboardInterrupt:
        input("\nTerminato. Premere un tasto per continuare")
        return "MAIN_MENU"

def ssr_test(ssr, nome: str):
    print(f"Test SSR {nome}, acceso 10 secondi, spento 10 secondi.\nCTRL+C per terminare.")
    lastTime = time.time()
    ssr.LOW()
    print(f"SSR {nome} stato: {ssr.getState()}")
    try:
        while True:
            elapsedTime = time.time()
            deltaTime = elapsedTime - lastTime
            if deltaTime > 10:
                ssr.toggleState()
                print(f"SSR {nome} stato: {ssr.getState()}")
                lastTime = elapsedTime
        
    except KeyboardInterrupt:
        ssr.LOW()
        input("\nTerminato. Premere un tasto per continuare...")
        return "MAIN MENU"

def dht22_test(dht, sampling):
    print("Test sensore DHT22.\nCTRL+C per terminare.")
    try:
        while True:
            temp = dht.getTemperature()
            hum = dht.getHumidity()
            print(f"Lettura DHT22: Temperatura {temp:.1f}°C | Umidità {hum:.1f}.")
            time.sleep(sampling)
    except KeyboardInterrupt:
        input("\nTerminato. Premere un tasto per continuare...")
        return "MAIN MENU"

def pzem_test(sensor, sampling):
    print("Test sensore PZEM004T.\nCTRL+C per terminare.")
    try:
        while True:
            (voltage, current, power, regpower) = sensor.readAll()
            print(f"Voltage: {voltage}, Current: {current}, Power: {power}, RegPower: {regpower}")
            time.sleep(sampling)
    except KeyboardInterrupt:
        input("\nTerminato. Premere un tasto per continuare...")
        return "MAIN MENU"

def pzem2_test(sensor, sampling):
    print("Test sensore PZEM004T Modbus.\nCTRL+C per terminare.")
    try:
        while True:
            readings = sensor.readAll()
            print(f"V: {readings['voltage']}V, I: {readings['current']}A, P: {readings['power']}W, E: {readings['energy']}J, F: {readings['frequency']}Hz, PF: {readings['powerfactor']}?, Alarm: {readings['alarm']}")
            time.sleep(sampling)
    except KeyboardInterrupt:
        input("\nTerminato. Premere un tasto per continuare...")
        return "MAIN MENU"
    
    
with open("config.json") as configFile:
    configData = json.load(configFile)
    
TC_SCK = configData["TC_PIN_SCK"]
TC_CS = configData["TC_PIN_CS"]
TC_DO = configData["TC_PIN_DO"]
RES_SSR_PIN = configData["RES_SSR_PIN"]
FAN_SSR_PIN = configData["FAN_SSR_PIN"]
DHT22_PIN = configData["DHT22_PIN"]
interval = configData["sample_interval"]
sample_size = configData["avg_sample_size"]
sampling = 0.3

tc = Termocoppia(TC_SCK,TC_CS,TC_DO, sample_size)
#dht22 = DHT22(DHT22_PIN)
ssr_res = SolidStateRelay(RES_SSR_PIN)
ssr_fan = SolidStateRelay(FAN_SSR_PIN)
#pzem = PZEM004T(configData["PZEM_port"], configData["PZEM_timeout"])
#pzem2 = PZEM004TModbus() #alternativa da controllare

m = TextMenu("Menu principale",ANSI.CYAN, ANSI.WHITE)
m.add_option("1","Test Termocoppia", partial(tc_test, sampling))
m.add_option("2","SSR Resistenze", partial(ssr_test, ssr_res, "Resistenze"))
m.add_option("3","SSR Ventola", partial(ssr_test, ssr_fan, "Ventola"))
#m.add_option("4","Sensore DHT22", partial(dht22_test, dht22, sampling))
#m.add_option("5","Sensore PZEM004T", partial(pzem_test, pzem, sampling))
#m.add_option("6","Sensore PZEM004T Modbus", partial(pzem2_test, pzem2, sampling))


m.run()


