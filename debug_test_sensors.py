from thermocouple import Termocoppia
from ss_relay import SolidStateRelay
from console_menu import TextMenu, ANSI
from functools import partial
from temp_sensor import TempSensor
#from customlib.PZEM004Tlib import PZEM004T
#from customlib.PZEM004TModbuslib import PZEM004TModbus
import json, time, sys, os


if os.name=="nt":#windows
    import msvcrt
    def get_key():
        if msvcrt.kbhit():
            return msvcrt.getch().decode(errors="ignore")
        return None
    INTERRUPT_KEY = "s"
else:
    import select, termios, tty
    def get_key():
        dr, _, _ =select.select([sys.stdin], [], [], 0)
        if dr:
            old = termios.tcgetattr(sys.stdin)
            try:
                tty.setcbreak(sys.stdin.fileno())
                return sys.stdin.read(1)
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old)
        return None
    INTERRUPT_KEY = "\x13"
    

def tc_test(sampling:float) -> str:
    try:
        print("Test Termocoppia.\nCTRL+C per terminare.")
        if tc._inizializza(sampling, debug=True) is not None:
            print("\n")
            while True:
                t = tc._read_tc()
                temp = tc.read_temp_average()
                print(f"Buffer: {tc.buffer}  |  LastTemp: {t}  | LastAVG: {temp}")
                time.sleep(sampling)
        else:
            input("Sonda non rilevata, programma terminato.\nPremere un tasto per continuare...")
            return "MAIN_MENU"
    except KeyboardInterrupt:
        input("\nTerminato. Premere un tasto per continuare")
        return "MAIN_MENU"


def ssr_test(ssr: SolidStateRelay, nome: str) -> str:
    print(f"Test SSR {nome}, acceso 10 secondi, spento 10 secondi.\nCTRL+C per terminare.")
    last_time = time.time()
    ssr.LOW()
    print(f"SSR {nome} stato: {ssr.get_state()}")
    try:
        while True:
            elapsed_time = time.time()
            delta_time = elapsed_time - last_time
            if delta_time > 10:
                ssr.toggle_state()
                print(f"SSR {nome} stato: {ssr.get_state()}")
                last_time = elapsed_time
        
    except KeyboardInterrupt:
        ssr.LOW()
        input("\nTerminato. Premere un tasto per continuare...")
        return "MAIN MENU"


def dht22_test(dht:TempSensor, sampling:float) -> str:
    print("Test sensore DHT22.\nCTRL+C per terminare.")
    try:
        while True:
            temp = dht.get_temperature()
            hum = dht.get_humidity()
            print(f"Lettura DHT22: Temperatura {temp:.1f}°C | Umidità {hum:.1f}.")
            time.sleep(sampling)
    except KeyboardInterrupt:
        input("\nTerminato. Premere un tasto per continuare...")
        return "MAIN MENU"


def pzem_test(sensor, sampling:float) -> str:
    #TODO change sensor type
    print("Test sensore PZEM004T.\nCTRL+C per terminare.")
    try:
        while True:
            (voltage, current, power, reg_power) = sensor.readAll()
            print(f"Voltage: {voltage}, Current: {current}, Power: {power}, RegPower: {reg_power}")
            time.sleep(sampling)
    except KeyboardInterrupt:
        input("\nTerminato. Premere un tasto per continuare...")
        return "MAIN MENU"


def pzem2_test(sensor, sampling:float) -> str:
    #TODO change sensor type
    print("Test sensore PZEM004T Modbus.\nCTRL+C per terminare.")
    try:
        while True:
            readings = sensor.readAll()
            print(f"V: {readings['voltage']}V, I: {readings['current']}A, P: {readings['power']}W, E: {readings['energy']}J, F: {readings['frequency']}Hz, PF: {readings['powerfactor']}?, Alarm: {readings['alarm']}")
            time.sleep(sampling)
    except KeyboardInterrupt:
        input("\nTerminato. Premere un tasto per continuare...")
        return "MAIN MENU"


def temp_test(sampling:float) -> None:
    print("=== TEST SONDA ===")
    print("CTRL+S → interrompe il ciclo e chiede nuova temperatura")
    print("CTRL+C → termina il test\n")    
    while True:
        try:
            try:
                target = float(input("Inserisci temperatura:" ))
            except ValueError:
                print("Valore non valido")
                continue
            
            print(f"\nAvvio ciclo per {target}°C...")
            print("Premi CTRL+S per interrompere il ciclo corrente.\n")
            
            stop_cycle:bool = False

            # --- CICLO DI RISCALDAMENTO ---
            counter:int = 0
            while True:
                # lettura temperatura
                counter +=1
                temp = tc.read_temp_average()
                if temp is None:
                    temp = float(0)

                # stampa stato
                print(f"\rTemp attuale: {temp}°C   Target: {target}°C | Counter: {counter}", end="")

                # controllo raggiungimento
                if temp >= target:
                    print("\nTarget raggiunto. Inizio mantenimento...")
                    break

                # controllo CTRL+S
                key = get_key()
                if key == INTERRUPT_KEY:  # CTRL+S
                    stop_cycle = True
                    print("\nInterruzione ciclo (CTRL+S).")
                    break

                time.sleep(sampling)

            # se CTRL+S → torna a chiedere nuova temperatura
            if stop_cycle:
                continue

            # --- CICLO DI MANTENIMENTO ---
            print("Mantenimento in corso... (CTRL+S per interrompere)")

            while True:
                temp = tc.read_temp_average()
                if temp is None:
                    temp = float(0)
                print(f"\rTemp attuale: {temp}°C   (mantenimento)", end="")

                # esempio: mantieni ±3°C
                if temp < target - 3:
                    print("\nTemperatura scesa troppo. Fine mantenimento.")
                    break

                # controllo CTRL+S
                key = get_key()
                if key == INTERRUPT_KEY:  # CTRL+S
                    stop_cycle = True
                    print("\nInterruzione ciclo (CTRL+S).")
                    break

                time.sleep(sampling)

            # se CTRL+S → torna a chiedere nuova temperatura
            if stop_cycle:
                continue

            print("\nCiclo completato.\n")

        except KeyboardInterrupt:
            print("\n\nTest interrotto manualmente (CTRL+C).")
            print("Uscita dal test sonda.")
            break    
        
with open("config.json") as config_file:
    config_data = json.load(config_file)
    
TC_SCK = config_data["TC_PIN_SCK"]
TC_CS = config_data["TC_PIN_CS"]
TC_DO = config_data["TC_PIN_DO"]
RES_SSR_PIN = config_data["RES_SSR_PIN"]
FAN_SSR_PIN = config_data["FAN_SSR_PIN"]
DHT22_PIN = config_data["DHT22_PIN"]
interval = config_data["sample_interval"]
sample_size = config_data["avg_sample_size"]
sampling = 0.3

tc = Termocoppia(TC_SCK,TC_CS,TC_DO, sample_size)
dht22 = TempSensor(DHT22_PIN)
ssr_res = SolidStateRelay(RES_SSR_PIN)
ssr_fan = SolidStateRelay(FAN_SSR_PIN)
#pzem = PZEM004T(configData["PZEM_port"], configData["PZEM_timeout"])
#pzem2 = PZEM004TModbus() #alternativa da controllare

m = TextMenu("Menu principale",ANSI.CYAN, ANSI.WHITE)
m.add_option("1","Test Termocoppia", partial(tc_test, sampling))
m.add_option("2","SSR Resistenze", partial(ssr_test, ssr_res, "Resistenze"))
m.add_option("3","SSR Ventola", partial(ssr_test, ssr_fan, "Ventola"))
m.add_option("4","Sensore DHT22", partial(dht22_test, dht22, sampling))
#m.add_option("5","Sensore PZEM004T", partial(pzem_test, pzem, sampling))
#m.add_option("6","Sensore PZEM004T Modbus", partial(pzem2_test, pzem2, sampling))
m.add_option("7","Test temperatura", partial(temp_test, sampling))

if __name__ == '__main__':
    m.run()
