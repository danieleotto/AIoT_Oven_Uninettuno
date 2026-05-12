from thermocouple import Termocoppia
from ss_relay import SolidStateRelay
from console_menu import TextMenu, ANSI
from functools import partial
from temp_sensor import TempSensor
from customlib.exceptions import ErroreSonda
from customlib.pzem004t_lib import PZEM004T
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
    

def tc_test(sampling_time:float) -> str:
    try:
        print("Test Termocoppia.\nCTRL+C per terminare.")
        if tc.controllo_sonda(sampling_time, debug=True) is not None:
            print("\n")
            while True:
                t = tc.read_raw_temp()
                temp = tc.read_temp_average()
                print(f"Buffer: {tc.buffer}  |  LastTemp: {t:.1f}  | LastAVG: {temp:.1f}")
                time.sleep(sampling_time)
        else:
            raise ErroreSonda
        
    except KeyboardInterrupt:
        input("\nTerminato. Premere un tasto per continuare")
        return "MAIN_MENU"
    except ErroreSonda:
        input("Sonda non rilevata, programma terminato.\nPremere un tasto per continuare...")
        return "MAIN_MENU"


def ssr_test(ssr: SolidStateRelay, nome: str) -> str:
    print(f"Test SSR {nome}, acceso 10 secondi, spento 10 secondi.\nCTRL+C per terminare.")
    last_time:float = time.time()
    remaining:float = 0.0
    ssr.turn_off()
    try:
        while True:
            elapsed_time = time.time()
            delta_time = elapsed_time - last_time
            if delta_time > 10:
                ssr.toggle_state()
                last_time = elapsed_time
            else:
                remaining = 10 - (delta_time % 10)
            print(f"SSR {nome} stato: {ssr.get_state()} | cambio in {remaining:.0f} s.")
            sys.stdout.write("\033[F\033[K")
        
    except KeyboardInterrupt:
        ssr.turn_off()
        input("\nTerminato. Premere un tasto per continuare...")
        return "MAIN_MENU"


def dht22_test(dht:TempSensor, sampling_time:float) -> str:
    print("Test sensore DHT22.\nCTRL+C per terminare.")
    try:
        while True:
            temp = dht.get_temperature()
            hum = dht.get_humidity()
            print(f"Lettura DHT22: Temperatura {temp:.1f}°C | Umidità {hum:.1f}.")
            time.sleep(sampling_time)
    except KeyboardInterrupt:
        input("\nTerminato. Premere un tasto per continuare...")
        return "MAIN_MENU"


def pzem_test(sensor, sampling_time:float) -> str:
    #TODO change sensor type
    print("Test sensore PZEM004T.\nCTRL+C per terminare.")
    try:
        while True:
            (voltage, current, power, reg_power) = sensor.read_all()
            print(f"Voltage: {voltage}, Current: {current}, Power: {power}, RegPower: {reg_power}")
            time.sleep(sampling_time)
    except KeyboardInterrupt:
        input("\nTerminato. Premere un tasto per continuare...")
        return "MAIN MENU"


# def pzem2_test(sensor, sampling_time:float) -> str:
#     #TODO change sensor type
#     print("Test sensore PZEM004T Modbus.\nCTRL+C per terminare.")
#     try:
#         while True:
#             readings = sensor.readAll()
#             print(f"V: {readings['voltage']}V, I: {readings['current']}A, P: {readings['power']}W, E: {readings['energy']}J, F: {readings['frequency']}Hz, PF: {readings['powerfactor']}?, Alarm: {readings['alarm']}")
#             time.sleep(sampling_time)
#     except KeyboardInterrupt:
#         input("\nTerminato. Premere un tasto per continuare...")
#         return "MAIN MENU"


def cycle_test(sampling_time:float, ssr:SolidStateRelay) -> str:
    print("=== TEST SONDA ===")
    print("S → interrompe il ciclo e chiede nuova temperatura")
    print("CTRL+C → termina il test\n")    
    while True:
        try:
            try:
                target = float(input("Inserisci temperatura:" ))
            except ValueError:
                print("Valore non valido")
                continue
            
            print(f"\nAvvio ciclo per {target}°C...")
            print("Premi S per interrompere il ciclo corrente.\n")
            stop_cycle:bool = False

            # --- CICLO DI RISCALDAMENTO ---
            temp = tc.read_temp_safe()
            while temp < target:
                ssr.turn_on()
                temp = tc.read_temp_safe()
                if temp is None:
                    temp = float(0)
                print(f"\rTemp attuale: {temp:.1f}°C   Target: {target:.1f}°C", end="")

                # controllo CTRL+S
                key = get_key()
                if key == INTERRUPT_KEY:  # CTRL+S
                    stop_cycle = True
                    print("\nInterruzione ciclo (S).")
                    break

                time.sleep(sampling_time)
            # se CTRL+S → torna a chiedere nuova temperatura
            if stop_cycle:
                continue
            ssr.turn_off()
            print("\nTarget raggiunto. Inizio mantenimento...\n")
            
            # --- CICLO DI MANTENIMENTO ---
            print("Mantenimento in corso... (S per interrompere)")
            while True:
                temp = tc.read_temp_average()
                if temp is None:
                    temp = float(0)
                print(f"\rTemp attuale: {temp:.1f}°C   (mantenimento)", end="")

                # controllo temperatura
                if temp >= target - 1:
                    ssr.turn_off()
                elif target - 5 < temp < target -1:
                    ssr.turn_on()
                elif temp <= target - 5:
                    print("\nTemperatura scesa troppo. Fine mantenimento.")
                    break

                # controllo CTRL+S
                key = get_key()
                if key == INTERRUPT_KEY:  # CTRL+S
                    stop_cycle = True
                    print("\nInterruzione ciclo (S).")
                    break

                time.sleep(sampling)

            # se CTRL+S → torna a chiedere nuova temperatura
            if stop_cycle:
                continue
            
            ssr.turn_off()
            print("\nCiclo completato.\n")
            break

        except KeyboardInterrupt:
            ssr.turn_off()
            print("\n\nTest interrotto manualmente (CTRL+C).")
            print("Uscita dal test sonda.")
            break
    return "MAIN MENU"


def ssr_state(is_on:bool, ssr_r:SolidStateRelay ,ssr_f:SolidStateRelay) -> str:
    if is_on:
        ssr_r.turn_on()
        ssr_f.turn_on()
    else:
        ssr_r.turn_off()
        ssr_f.turn_off()
    print(f"SSR Res: {ssr_r.get_state()} | SSR Fan: {ssr_f.get_state()}")
    input("Premere un tasto per continuare...")
    return "MAIN_MENU"

       
       
        
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
sampling = config_data["sample_interval"]

tc = Termocoppia(TC_SCK,TC_CS,TC_DO, sample_size)
dht22 = TempSensor(DHT22_PIN)
ssr_res = SolidStateRelay(RES_SSR_PIN)
ssr_fan = SolidStateRelay(FAN_SSR_PIN)
pzem = PZEM004T(config_data["PZEM_port"], config_data["PZEM_timeout"])
#pzem2 = PZEM004TModbus() #alternativa da controllare

m = TextMenu("Menu principale",ANSI.CYAN, ANSI.WHITE)
m.add_option("1","Test Termocoppia", partial(tc_test, sampling))
m.add_option("2","SSR Resistenze", partial(ssr_test, ssr_res, "Resistenze"))
m.add_option("3","SSR Ventola", partial(ssr_test, ssr_fan, "Ventola"))
m.add_option("4","Sensore DHT22", partial(dht22_test, dht22, sampling))
m.add_option("5","Sensore PZEM004T", partial(pzem_test, pzem, sampling))
#m.add_option("6","Sensore PZEM004T Modbus", partial(pzem2_test, pzem2, sampling))
m.add_option("7","Test Ciclo Riscaldamento", partial(cycle_test, sampling, ssr_res))
m.add_option("8","Forza tutti SSR on", partial(ssr_state, True, ssr_res, ssr_fan))
m.add_option("9","Forza tutti SSR off", partial(ssr_state, False, ssr_res, ssr_fan))

if __name__ == '__main__':
    m.run()
    ssr_res.turn_off()
    ssr_fan.turn_off()