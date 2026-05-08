import wiringpi as wp
from wiringpi import GPIO

class SolidStateRelay:
    def __init__(self, PIN:int) -> None:
        self.PIN = PIN
        self.is_On:bool = False

        wp.wiringPiSetup()
        wp.pinMode(self.PIN, GPIO.OUTPUT)
        wp.digitalWrite(self.PIN, GPIO.LOW)


    def turn_off(self) -> None:
        wp.digitalWrite(self.PIN, GPIO.LOW)
        self.is_On = False

    
    def request_off(self) -> None:
        if self.get_state() == True:
            self.turn_off()


    def turn_on(self) -> None:
        wp.digitalWrite(self.PIN, GPIO.HIGH)
        self.is_On = True

            
    def request_on(self) -> None:
        if self.get_state() == False:
            self.turn_on()


    def get_state(self) -> bool:
        if self.is_On:
            return True
        else:
            return False
    
    
    def toggle_state(self) -> None:
        if self.get_state():
            self.turn_off()
        else:
            self.turn_on()