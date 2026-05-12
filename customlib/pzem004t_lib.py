import serial, struct, time

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

    def check_checksum(self, _tuple):
        _list = list(_tuple)
        _checksum = _list[-1]
        _list.pop()
        _sum = sum(_list)
        if _checksum == _sum%256:
            return True
        else:
            raise Exception("Wrong Checksum")

    def is_ready(self):
        self.ser.write(serial.to_bytes(self.setAddressBytes))
        print("Debug sono qui")
        time.sleep(1)
        rcv = self.ser.read(7)
        print(rcv)
        time.sleep(1)
        if len(rcv) == 7:
            unpacked = struct.unpack("!7B", rcv)
            if self.check_checksum(unpacked):
                return True
            else:
                return False
        else:
            raise serial.SerialTimeoutException("Timeout setting address")

    def read_voltage(self):
        self.ser.write(serial.to_bytes(self.readVoltageBytes))
        rcv = self.ser.read(7)
        if len(rcv) == 7:
            unpacked = struct.unpack("!7B", rcv)
            if self.check_checksum(unpacked):
                tension = unpacked[2]+unpacked[3]/10.0
                return tension
            else:
                raise Exception("Wrong Checksum")
        else:
            raise serial.SerialTimeoutException("Timeout reading voltage")

    def read_current(self):
        self.ser.write(serial.to_bytes(self.readCurrentBytes))
        rcv = self.ser.read(7)
        if len(rcv) == 7:
            unpacked = struct.unpack("!7B", rcv)
            if self.check_checksum(unpacked):
                current = unpacked[2]+unpacked[3]/100.0
                return current
            else:
                raise Exception("Wrong Checksum")
        else:
            raise serial.SerialTimeoutException("Timeout reading current")

    def read_power(self):
        self.ser.write(serial.to_bytes(self.readPowerBytes))
        rcv = self.ser.read(7)
        if len(rcv) == 7:
            unpacked = struct.unpack("!7B", rcv)
            if self.check_checksum(unpacked):
                power = unpacked[1]*256 + unpacked[2]
                return power
            else:
                raise Exception("Wrong Checksum")
        else:
            raise serial.SerialTimeoutException("Timeout reading power")

    def read_reg_power(self):
        self.ser.write(serial.to_bytes(self.readRegPowerBytes))
        rcv = self.ser.read(7)
        if len(rcv) == 7:
            unpacked = struct.unpack("!7B", rcv)
            if self.check_checksum(unpacked):
                regPower = unpacked[1]*256*256 + unpacked[2]*256 + unpacked[3]
                return regPower
            else:
                raise Exception("Wrong Checksum")
        else:
            raise serial.SerialTimeoutException("Timeout reading registered power")

    def read_all(self):
        if self.is_ready():
            return self.read_voltage(), self.read_current(), self.read_power(), self.read_reg_power()
        else:
            raise serial.SerialTimeoutException("Timeout reading address")

    def close(self):
        self.ser.close()
