import wiringpi as wp
from wiringpi import GPIO

class SSR(object):
    def __init__(self, PIN):
        self.PIN = PIN
        self.isOn = False

        wp.wiringPiSetup()
        wp.pinMode(self.PIN, GPIO.OUTPUT)
        wp.digitalWrite(self.PIN, GPIO.LOW)


    def LOW(self):
        wp.pinMode(self.PIN, GPIO.LOW)
        self.isOn = False

    def HIGH(self):
        wp.pinMode(self.PIN, GPIO.HIGH)
        self.isOn = True
