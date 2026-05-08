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
    minutes:float = 0
    hours:float = 0
    if timesec is None:
        return "Nan"
    elif 60 <= timesec < 3600:
        seconds = timesec % 60
        minutes = (timesec - seconds) / 60
    elif timesec >= 3600:
        seconds = timesec % 60
        minutes = ((timesec - seconds) / 60) % 60
        hours = (timesec - minutes - seconds) / 3600
    else:
        seconds = timesec
    if hours > 0:
        parts.append(f"{hours:.0f} [h]")
    if minutes > 0:
        parts.append(f"{min:.0f} [m]")
    if seconds > 0 and ms == False:
        parts.append(f"{seconds:.0f} [s]")
    else:
        parts.append(f"{seconds:.3f} [s]")
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