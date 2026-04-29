import os

def clear():
    os.system("clear" if os.name == "posix" else "cls")


class ANSI:
    RESET = "\033[0m"
    BOLD = "\033[1m"

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GREY = "\033[90m"

    BG_BLUE = "\033[44m"
    BG_CYAN = "\033[46m"


class TextMenu:
    def __init__(self, title="Menu", color_title=ANSI.CYAN, color_option=ANSI.WHITE):
        self.title = title
        self.options = {}
        self.exit_key = "0"
        self.parent = None
        
        self.color_title = color_title
        self.color_option = color_option
        
        
    def add_option(self, key, description, action, disabled = False, executable=False):
        self.options[key] = {
            "desc": description,
            "action": action,
            "disabled": disabled,
            "exec": executable
        }
        
        if isinstance(action, TextMenu):
            action.parent = self
           
            
    def show(self):
        clear ()
        
        print("\n"+"="*40)
        print(f"{self.color_title}{ANSI.BOLD}{self.title}{ANSI.RESET}")
        print("="*40)
        
        for key, opt in self.options.items():
            desc = opt["desc"]
            disabled = opt["disabled"]
            executable = opt["exec"]
            if callable(desc):
                desc = desc()
            if disabled:
                if executable:
                    print(f"\n{ANSI.GREY}[{key}] {desc} (disabilitato){ANSI.RESET}")
                else:
                    print(f"{ANSI.GREY}[{key}] {desc} (disabilitato){ANSI.RESET}")
            else:
                if executable:
                    print(f"\n{ANSI.GREEN}[{key}] {desc}{ANSI.RESET}")
                else:
                    print(f"{self.color_option}[{key}] {desc}{ANSI.RESET}")
        print("-"*40)
        if self.parent is None:
            print(f"{ANSI.YELLOW}[{self.exit_key}] Esci{ANSI.RESET}")
        else:
            print(f"{ANSI.YELLOW}[{self.exit_key}] Torna indietro{ANSI.RESET}")
        print("-"*40)
    
    
    def run(self):
        while True:
            self.show()
            choice = input("Seleziona un'opzione: ").strip()
            
            if choice == self.exit_key:
                if self.parent is None:
                    print(f"{ANSI.RED}Uscita dal programma.{ANSI.RESET}")
                    break
                else:
                    return
                
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
            else:
                print(f"{ANSI.RED}Scelta non valida.{ANSI.RESET}")
                input("Premi invio per continuare...")