from typing import Any

from customlib.functions import clear_console

class ANSI:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GREY = "\033[90m"

    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"  
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"
    BG_GRAY = "\033[100m"
    


class TextMenu:
    def __init__(self, title:str = "Menu", color_title:str = ANSI.CYAN, color_option:str = ANSI.WHITE) -> None:
        self.title = title
        self.options = {}
        self.exit_key = "Q"
        self.parent = None
        self.color_title = color_title
        self.color_option = color_option
        
        
    def add_option(self, key:str , description:str, action, disabled:bool = False, executable:bool = False) -> None:
        self.options[key] = {
            "desc": description,
            "action": action,
            "disabled": disabled,
            "exec": executable
        }       
        if isinstance(action, TextMenu):
            action.parent = self        
       
            
    def show(self) -> None:
        clear_console()
        
        print("\n"+"="*50)
        print(f"{self.color_title}{ANSI.BOLD}{self.title}{ANSI.RESET}")
        print("="*50)
        
        for key, opt in self.options.items():
            desc:Any = opt["desc"]
            disabled:str = opt["disabled"]
            is_executable:bool = opt["exec"]
            if callable(desc):
                desc = desc()
            else:
                desc = str(desc)
            if disabled:
                if is_executable:
                    print(f"\n{ANSI.GREY}[{key}] {desc} (disabilitato){ANSI.RESET}")
                else:
                    print(f"{ANSI.GREY}[{key}] {desc} (disabilitato){ANSI.RESET}")
            else:
                if is_executable:
                    print(f"\n{ANSI.GREEN}[{key}] {desc}{ANSI.RESET}")
                else:
                    print(f"{self.color_option}[{key}] {desc}{ANSI.RESET}")
        print("-"*50)
        if self.parent is None:
            print(f"{ANSI.YELLOW}[{self.exit_key}] Esci{ANSI.RESET}")
        else:
            print(f"{ANSI.YELLOW}[{self.exit_key}] Torna indietro{ANSI.RESET}")
        print("-"*50)
    
    
    def run(self) -> str | None:
        while True:
            self.show()
            choice = input("Seleziona un'opzione: ").strip().upper()
            
            if choice == self.exit_key:
                if self.parent is None:
                    print(f"{ANSI.RED}Uscita dal programma.{ANSI.RESET}")
                    break
                else:
                    return None
                
            if choice in self.options:
                opt = self.options[choice]
                if opt["disabled"]:
                    print(f"{ANSI.RED}Questa voce è disabilitata.{ANSI.RESET}")
                    input("Invio per continuare...")
                    continue
                action = opt["action"]
                
                if isinstance(action, TextMenu):
                    result = action.run()
                else:
                    result = action()

                if result == "MAIN_MENU":
                    if self.parent is None:
                        continue
                    else:
                        return "MAIN_MENU"
                
                if result == "BACK":
                    return None
            else:
                print(f"{ANSI.RED}Scelta non valida.{ANSI.RESET}")
                input("Premi invio per continuare...")
    
    
    def enable_exec(self) -> None:
        for key,opt in self.options.items():
            if opt["exec"]:
                opt["disabled"] = False
    
    
    def disable_exec(self) -> None:
        for key,opt in self.options.items():
            if opt["exec"]:
                opt["disabled"] = True

            