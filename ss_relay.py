import wiringpi as wp
from wiringpi import GPIO

class SolidStateRelay:
    def __init__(self, PIN:int) -> None:
        self.PIN = PIN
        self.is_On:bool = False

        wp.wiringPiSetup()
        wp.pinMode(self.PIN, GPIO.OUTPUT)
        wp.digitalWrite(self.PIN, GPIO.LOW)


    def LOW(self) -> None:
        wp.digitalWrite(self.PIN, GPIO.LOW)
        self.is_On = False


    def HIGH(self) -> None:
        wp.digitalWrite(self.PIN, GPIO.HIGH)
        self.is_On = True


    def get_state(self) -> bool:
        if self.is_On:
            return True
        else:
            return False
    
    
    def toggle_state(self) -> None:
        if self.get_state():
            self.LOW()
        else:
            self.HIGH()