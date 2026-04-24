import time
import serial
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu

class PZEM004TModbus:
    def __init__(self):
        self.serial = serial.Serial(
            port = '/dev/ttyS0',
            baudrate = 9600,
            bytesize = 8,
            parity = 'N',
            stopbits = 1,
            xonxoff = False,
        )
        self.master = modbus_rtu.RtuMaster(self.serial)
        self.master.set_timeout(2.0)
        self.master.set_timeout(True)

    def readAll(self):
        data = self.master.execute(1, cst.READ_INPUT_REGISTERS,0,10)
        voltage = data[0] / 10.0 #[V]
        current = (data[1] + (data[2] << 16)) / 1000.0 #[A]
        power = (data[3] + (data[4] << 16)) / 10.0 #[W]
        energy = data[5] + (data[6] << 16) #[Wh]
        frequency = data[7] / 10.0 #[Hz]
        powerfactor = data[8] / 100.0
        alarm = data[9] # 0 = no alarm
        readings = {'voltage':voltage, 'current':current, 'power':power, 'energy':energy, 'frequency':frequency, 'powerfactor': powerfactor, 'alarm':alarm}
        return readings

    def getVoltage(self):
        readings = self.readAll()
        return readings['voltage']

    def getCurrent(self):
        readings = self.readAll()
        return readings['current']

    def getPower(self):
        readings = self.readAll()
        return readings['power']

    def getEnergy(self):
        readings = self.readAll()
        return readings['energy']

    def getFrequency(self):
        readings = self.readAll()
        return readings['frequency']

    def getPowerFactor(self):
        readings = self.readAll()
        return readings['powerfactor']

    def getAlarm(self):
        readings = self.readAll()
        return readings['alarm']

