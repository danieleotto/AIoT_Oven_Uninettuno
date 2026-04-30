from consoleMenu import TextMenu, ANSI
from processi import Essicatura,Ricottura,SaldaturaSMD


eProc = Essicatura()
rProc = Ricottura()
sProc = SaldaturaSMD()
menu_principale = TextMenu("Menu Principale - Scelta Processo", color_title=ANSI.GREEN, color_option=ANSI.CYAN)
menu_principale.add_option("1", "Essicatura", eProc.textMenu)
menu_principale.add_option("2", "Ricottura", rProc.textMenu)
menu_principale.add_option("3", "Saldatura SMD", sProc.textMenu)

menu_principale.run()
