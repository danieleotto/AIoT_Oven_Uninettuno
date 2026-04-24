import serial, struct
import serial.serialutil


class PZEM004T:
    setAddressBytes     = [0xB4,0xC0,0xA8,0x01,0x01,0x00,0x1E]
    readVoltageBytes    = [0xB0,0xC0,0xA8,0x01,0x01,0x00,0x1A]
    readCurrentBytes    = [0xB1,0xC0,0xA8,0x01,0x01,0x00,0x1B]
    readPowerBytes      = [0xB2,0xC0,0xA8,0x01,0x01,0x00,0x1C]
    readRegPowerBytes   = [0xB3,0xC0,0xA8,0x01,0x01,0x00,0x1D]

    def __init__(self, port, timeout):
        self.ser = serial.Serial(
            port=port,
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=timeout
        )
        if self.ser.is_open:
            self.ser.close()
        self.ser.open()

    def checkChecksum(self, _tuple):
        _list = list(_tuple)
        _checksum = _list[-1]
        _list.pop()
        _sum = sum(_list)
        if _checksum == _sum%256:
            return True
        else:
            raise Exception("Wrong Checksum")

    def isReady(self):
        self.ser.write(serial.to_bytes(self.setAddressBytes))
        rcv = self.ser.read(7)
        if len(rcv) == 7:
            unpacked = struct.unpack("!7B", rcv)
            if self.checkChecksum(unpacked):
                return True
            else:
                return False
        else:
            raise serial.SerialTimeoutException("Timeout setting address")

    def readVoltage(self):
        self.ser.write(serial.to_bytes(self.readVoltageBytes))
        rcv = self.ser.read(7)
        if len(rcv) == 7:
            unpacked = struct.unpack("!7B", rcv)
            if self.checkChecksum(unpacked):
                tension = unpacked[2]+unpacked[3]/10.0
                return tension
            else:
                raise Exception("Wrong Checksum")
        else:
            raise serial.SerialTimeoutException("Timeout reading voltage")

    def readCurrent(self):
        self.ser.write(serial.to_bytes(self.readCurrentBytes))
        rcv = self.ser.read(7)
        if len(rcv) == 7:
            unpacked = struct.unpack("!7B", rcv)
            if self.checkChecksum(unpacked):
                current = unpacked[2]+unpacked[3]/100.0
                return current
            else:
                raise Exception("Wrong Checksum")
        else:
            raise serial.SerialTimeoutException("Timeout reading current")

    def readPower(self):
        self.ser.write(serial.to_bytes(self.readPowerBytes))
        rcv = self.ser.read(7)
        if len(rcv) == 7:
            unpacked = struct.unpack("!7B", rcv)
            if self.checkChecksum(unpacked):
                power = unpacked[1]*256 + unpacked[2]
                return power
            else:
                raise Exception("Wrong Checksum")
        else:
            raise serial.SerialTimeoutException("Timeout reading power")

    def readRegPower(self):
        self.ser.write(serial.to_bytes(self.readRegPowerBytes))
        rcv = self.ser.read(7)
        if len(rcv) == 7:
            unpacked = struct.unpack("!7B", rcv)
            if self.checkChecksum(unpacked):
                regPower = unpacked[1]*256*256 + unpacked[2]*256 + unpacked[3]
                return regPower
            else:
                raise Exception("Wrong Checksum")
        else:
            raise serial.SerialTimeoutException("Timeout reading registered power")

    def readAll(self):
        if self.isReady():
            return self.readVoltage(), self.readCurrent(), self.readPower(), self.readRegPower()
        else:
            raise serial.SerialTimeoutException("Timeout reading address")

    def close(self):
        self.ser.close()
