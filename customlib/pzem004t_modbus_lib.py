from pymodbus.client import ModbusSerialClient


class PZEM004TModbus:
    def __init__(self, port:str = "/dev/ttyUSB0",timeout:float = 0.3, dev_id:int = 248):
        self.port = port
        self.timeout = timeout
        self.dev_id = dev_id
        self.client = ModbusSerialClient(
            port=self.port,
            baudrate=9600,
            parity='N',
            stopbits=1,
            bytesize=8,
            timeout=self.timeout
        )
        try:
            self.client.close()
        except:
            pass
        self.client.connect()
               

    def readAll(self):
        result = self.client.read_input_registers(address=0, count=10, device_id=self.dev_id)
        if result.isError():
            raise Exception("Errore Modbus")
        
        data = result.registers
        voltage = data[0] / 10.0 #[V]
        current = (data[1] + (data[2] << 16)) / 1000.0 #[A]
        power = (data[3] + (data[4] << 16)) / 10.0 #[W]
        energy = data[5] + (data[6] << 16) #[Wh]
        frequency = data[7] / 10.0 #[Hz]
        powerfactor = data[8] / 100.0
        alarm = data[9] # 0 = no alarm
        return {
            'voltage':voltage,
            'current':current,
            'power':power,
            'energy':energy,
            'frequency':frequency,
            'powerfactor': powerfactor,
            'alarm':alarm
        }
        

    def getVoltage(self):
        return self.readAll()['voltage']

    def getCurrent(self):
        return self.readAll()['current']

    def getPower(self):
        return self.readAll()['power']

    def getEnergy(self):
        return self.readAll()['energy']

    def getFrequency(self):
        return self.readAll()['frequency']

    def getPowerFactor(self):
        return self.readAll()['powerfactor']

    def getAlarm(self):
        return self.readAll()['alarm']

    def __del__(self):
        try:
            if self.client:
                self.client.close()
        except:
            pass
