from menu import TextMenu, ANSI
from functools import partial
from processi import Essicatura
import time, os

def clear():
    os.system("clear" if os.name == "posix" or "cls")

def ricottura():
    print(f"Processo Ricottura: PLACEHOLDER TODO\n")
    time.sleep(2)
    return "MAIN_MENU"

def saldatura():
    print(f"Processo Saldatura SMD: PLACEHOLDER TODO\n")
    time.sleep(2)

def donot():
    print("Do Nothing")
    time.sleep(2)
    
def todo(text):
    print(f"Parametro passato: {text}")
    time.sleep(2)
    


def setTemp(params, menu=None, key=None):
    try:
        t = float(input("Temperatura target: "))
        params.valori["temperatura"] = t
        if menu:
            aggiorna_menu(menu, key, params)
    except:
        print("Valore non valido.")
        print("Invio per continuare...")

def setTime(params, menu=None, key=None):
    try:
        t = float(input("Durata processo: "))
        params.valori["durata"] = t
        if menu:
            aggiorna_menu(menu, key, params)
    except:
        print("Valore non valido.")
        print("Invio per continuare...")

def aggiorna_menu(menu, key,  p):
    menu.options[key]["disabled"] = not p.completo()

def essicatura(params):
    clear()
    if not params.completo():
        print("Parametri incompleti!")
        print(params.valori)
        input("Invio per continuare...")
        return
    print("Avvio con parametri:")
    print(params.valori)
    t = params.valori["temperatura"]
    ti = params.valori["durata"]
    print(f"Impostata temperatura: {t} per {ti} secondi...")
    startTime = time.time()
    elapsedTime = 0
    while elapsedTime < ti:
        print(f"Temperatura: {t} | Tempo: {elapsedTime:.2f}.")
        time.sleep(0.2)
        elapsedTime = time.time() - startTime  
    print("Operazione terminata... ritorno al menu principale.")
    time.sleep(2)
    return "MAIN_MENU"

def ricottura(params):
    clear()
    if not params.completo():
        print("Parametri incompleti!")
        print(params.valori)
        input("Invio per continuare...")
        return
    print("Avvio con parametri:")
    print(params.valori)
    t = params.valori["temperatura"]
    ti = params.valori["durata"]
    print(f"Impostata temperatura: {t} per {ti} secondi...")
    startTime = time.time()
    elapsedTime = 0
    while elapsedTime < ti:
        print(f"Temperatura: {t} | Tempo: {elapsedTime:.2f}.")
        time.sleep(0.2)
        elapsedTime = time.time() - startTime  
    print("Operazione terminata... ritorno al menu principale.")
    time.sleep(2)
    return "MAIN_MENU"

eParams = Essicatura()
rParams = Essicatura()
menu_principale = TextMenu("Menu Principale - Scelta Processo", color_title=ANSI.GREEN, color_option=ANSI.CYAN)
menu_essicatura = TextMenu("Essicatura", color_title=ANSI.MAGENTA, color_option=ANSI.CYAN)
menu_ricottura = TextMenu("Ricottura", color_title=ANSI.MAGENTA, color_option=ANSI.CYAN)
menu_saldatura = TextMenu("Saldatura SMD", color_title=ANSI.MAGENTA, color_option=ANSI.CYAN)
menu_principale.add_option("1","Essicatura", menu_essicatura)
menu_principale.add_option("2", "Ricottura", menu_ricottura)
menu_principale.add_option("3", "Saldatura SMD", menu_saldatura)

menu_essicatura.add_option("1", lambda: f"Imposta Target Temp.: {eParams.valori['temperatura'] or '-'} [°C]", partial(setTemp, eParams, menu_essicatura, "3"))
menu_essicatura.add_option("2", lambda: f"Imposta Durata      : {eParams.valori['durata'] or '-'} [sec]", partial(setTime, eParams, menu_essicatura,"3"))
menu_essicatura.add_option("3", "Avvia", partial(essicatura, eParams), disabled=True, executable=True)

menu_ricottura.add_option("1", lambda: f"Imposta Target Temp.: {rParams.valori['temperatura'] or '-'} [°C]", partial(setTemp, rParams, menu_ricottura, "3"))
menu_ricottura.add_option("2", lambda: f"Imposta Durata      : {rParams.valori['durata'] or '-'} [sec]", partial(setTime, rParams, menu_ricottura,"3"))
menu_ricottura.add_option("3", "Avvia", partial(ricottura, rParams), disabled=True, executable=True)

menu_saldatura.add_option("1", "Avvia", saldatura)
menu_saldatura.add_option("2", "Placehold", donot)


menu_principale.run()
