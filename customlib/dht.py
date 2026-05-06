import time
import wiringpi as wp
from wiringpi import *

class DHTResult:
    ERR_NO_ERROR = 0
    ERR_MISSING_DATA = 1
    ERR_CRC = 2
    
    error_code = ERR_NO_ERROR
    temperature = -1
    humidity = -1
    
    def __init__(self, error_code, temperature, humidity):
        self.error_code = error_code
        self.temperature = temperature
        self.humidity = humidity
        
    def is_valid(self):
        return self.error_code == DHTResult.ERR_NO_ERROR
    

class DHT:
    __pin = 0 
    
    def __init__(self, pin, sensor=22):
        self.__pin = pin
        #Sensor should be set up to DHT11 or DHT22.
        if sensor in [22, 11]:
            self.__sensor = sensor
        else:
            raise ValueError('invalid sensor dht')
        wp.wiringPiSetup()
        
    def read(self):
        wp.pinMode(self.__pin, GPIO.OUTPUT)
        
        #send initial high
        self.__send_and_sleep(GPIO.HIGH, 0.05)
        
        #pull down to low
        self.__send_and_sleep(GPIO.LOW, 0.02)
        
        #change to input using pullup
        wp.pinMode(self.__pin, GPIO.INPUT)
        wp.pullUpDnControl(self.__pin,PUD_UP)
        
        #collect data into an array
        data = self.__collect_input()
        
        #parse lenghts of all data pull up periods
        pull_up_lenghts = self.__parse_data_pull_up_lenghts(data)
        
        #if bit count mismatch, return error (4 byte data + 1 byte checksum)
        #Fix issue on my board with AM2301 to ensure at least the data is available
        pull_up_lenghts_size = len(pull_up_lenghts)
        if (self.__sensor == 22 and pull_up_lenghts_size < 40) or (self.__sensor == 11 and pull_up_lenghts_size != 40):
            return DHTResult(DHTResult.ERR_MISSING_DATA, 0, 0)
        
        #calculate bits from lenghts of the pull up period
        bits = self.__calculate_bits(pull_up_lenghts)
        
        #we have the bits, calculate bytes
        the_bytes = self.__bits_to_bytes(bits)
        
        #calculate checksum and check
        checksum = self.__calculate_checksum(the_bytes)
        if the_bytes[4] != checksum:
            return DHTResult(DHTResult.ERR_CRC, 0, 0)
        
        if self.__sensor == 22:
            #compute to ensure negative values are taken into account
            c = (float)(((the_bytes[2]&0x7F) << 8) + the_bytes[3]) / 10
            
            #ok, we have valid data, return it
            if (c > 125):
                c = the_bytes[2]
            
            if (the_bytes[2] & 0x80):
                c = -c
                
            return DHTResult(DHTResult.ERR_NO_ERROR, c, ((the_bytes[0] << 8) + the_bytes[1]) / 10.00)
        else:
            #ok we have valid data, return it
            return DHTResult(DHTResult.ERR_NO_ERROR, the_bytes[2], the_bytes[0])
        
        
    def __send_and_sleep(self, output, sleep):
        wp.digitalWrite(self.__pin, output)
        time.sleep(sleep)


    def __collect_input(self):
        #collect the data while unchanged found
        unchanged_count = 0
        
        #this is used to determine where is the end of the data
        max_unchanged_count = 100
        
        last = -1
        data = []
        while True:
            current = wp.digitalRead(self.__pin)
            data.append(current)
            if last != current:
                unchanged_count = 0
                last = current
            else:
                unchanged_count += 1
                if unchanged_count > max_unchanged_count:
                    break
        
        return data
    
    
    def __parse_data_pull_up_lenghts(self, data):
        STATE_INIT_PULL_DOWN = 1
        STATE_INIT_PULL_UP = 2
        STATE_DATA_FIRST_PULL_DOWN = 3
        STATE_DATA_PULL_UP = 4
        STATE_DATA_PULL_DOWN = 5
        
        state = STATE_INIT_PULL_DOWN
        
        lenghts = [] #will contain the lenghts of the data pull up periods
        current_lenght = 0 #will contain the lenght of the previous period
        
        for i in range(len(data)):
            
            current = data[i]
            current_lenght += 1
            
            if state == STATE_INIT_PULL_DOWN:
                if current == GPIO.LOW:
                    #ok, we got the initial pull down
                    state = STATE_INIT_PULL_UP
                    continue
                else:
                    continue
            if state == STATE_INIT_PULL_UP:
                if current == GPIO.HIGH:
                    #ok, we got the initial pull up
                    state = STATE_DATA_FIRST_PULL_DOWN
                    continue
                else:
                    continue
            if state == STATE_DATA_FIRST_PULL_DOWN:
                if current == GPIO.LOW:
                    #we have initial pulldown, the next will be the data pull up
                    state = STATE_DATA_PULL_UP
                    continue
                else:
                    continue
            if state == STATE_DATA_PULL_UP:
                if current == GPIO.HIGH:
                    #data pulled up, th lenght of this pull will determine wheter is 0 or 1
                    current_lenght = 0
                    state = STATE_DATA_PULL_DOWN
                    continue
                else:
                    continue
            if state == STATE_DATA_PULL_DOWN:
                if current == GPIO.LOW:
                    #pulled down, we store the lenght of the previous pull up period
                    lenghts.append(current_lenght)
                    state = STATE_DATA_PULL_UP
                    continue
                else:
                    continue
                
        return lenghts
    
    
    def __calculate_bits(self, pull_up_lenghts):
        #find shortest and longest period
        shortest_pull_up = 1000
        longest_pull_up = 0
        
        for i in range(0, len(pull_up_lenghts)):
            lenght = pull_up_lenghts[i]
            if lenght < shortest_pull_up:
                shortest_pull_up = lenght
            if lenght > longest_pull_up:
                longest_pull_up = lenght
        
        #use the halfway to determine wheter the period is long or short
        halfway = shortest_pull_up + (longest_pull_up - shortest_pull_up) / 2
        bits = []
        
        for i in range(0, len(pull_up_lenghts)):
            bit = False
            if pull_up_lenghts[i] > halfway:
                bit = True
            bits.append(bit)
            
        return bits
    
    
    def __bits_to_bytes(self, bits):
        the_bytes = []
        byte = 0
        
        for i in range(0, len(bits)):
            byte = byte << 1
            if (bits[i]):
                byte = byte | 1
            else:
                byte = byte | 0
            if ((i+1) % 8 == 0):
                the_bytes.append(byte)
                byte = 0
                
        return the_bytes
    
    
    def __calculate_checksum(self, the_bytes):
        return the_bytes[0] + the_bytes[1] + the_bytes[2] + the_bytes[3] & 255