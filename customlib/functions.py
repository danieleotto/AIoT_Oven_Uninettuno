import os
from datetime import datetime


def todo_placeholder() -> None:
    input("Non ancora impelementato. Premere per continuare...")


def clear_console() -> None:
    os.system("clear" if os.name == "posix" else "cls")
    
 
def get_timestamp(readable:bool = True) -> str:
    if readable:
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    else:
        return datetime.now().isoformat()
 
    
def time_convert_str(timesec:float, ms:bool = False) -> str:
    parts:list = []
    sec:float = 0
    min:float = 0
    hr:float = 0
    if timesec is None:
        return None
    elif timesec >= 60 and timesec < 3600:
        sec = timesec % 60
        min = (timesec - sec)/60
    elif timesec >= 3600:
        sec = timesec % 60
        min = ((timesec - sec) / 60) % 60 
        hr = (timesec - min - sec)/3600
    else:
        sec = timesec
    if hr>0:
        parts.append(f"{hr:.0f} [h]")
    if min>0:
        parts.append(f"{min:.0f} [m]")
    if sec>0 and ms == False:
        parts.append(f"{sec:.0f} [s]")
    if sec>0 and ms == True:
        parts.append(f"{sec:.3f} [s]")
    return " ".join(parts)


def ask_continue(domanda:str, is_default_yes:bool = True) -> bool:
    risposte_ok:list = ["y"]
    risposte_not_ok:list = ["n"]
    if is_default_yes:
        risposte_ok.append("")
    else:
        risposte_not_ok.append("")

    while True:
        risposta = input(domanda).strip().lower()
        if risposta in risposte_ok:
            return True
        if risposta in risposte_not_ok:
            return False
        print("Answer not allowed. Press y or n.")