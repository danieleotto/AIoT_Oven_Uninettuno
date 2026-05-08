import wiringpi as wp
from wiringpi import GPIO

class SolidStateRelay:
    def __init__(self, pin:int) -> None:
        self.pin = pin
        self.is_On:bool = False

        wp.wiringPiSetup()
        wp.pinMode(self.pin, GPIO.OUTPUT)
        wp.digitalWrite(self.pin, GPIO.LOW)


    def turn_off(self) -> None:
        wp.digitalWrite(self.pin, GPIO.LOW)
        self.is_On = False

    
    def request_off(self) -> None:
        if self.get_state():
            self.turn_off()


    def turn_on(self) -> None:
        wp.digitalWrite(self.pin, GPIO.HIGH)
        self.is_On = True

            
    def request_on(self) -> None:
        if not self.get_state():
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