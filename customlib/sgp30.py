import time
from smbus2 import SMBus

class SGP30:
    ADDRESS = 0x58
    def __init__(self, bus_id=2):
        self.bus = SMBus(bus_id)
        self._iaq_init()


    @staticmethod
    def _crc8(data):
        crc = 0xFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc <<= 1
                crc &= 0xFF
        return crc


    def _iaq_init(self):
        self.bus.write_i2c_block_data(self.ADDRESS, 0x20, [0x03])
        time.sleep(0.01)


    def read(self):
        self.bus.write_i2c_block_data(self.ADDRESS, 0x20, [0x08])
        time.sleep(0.005)

        data = self.bus.read_i2c_block_data(self.ADDRESS, 0, 6)

        eco2 = (data[0] << 8) | data[1]
        if data[2] != self._crc8(data[:2]):
            return None, None

        tvoc = (data[3] << 8) | data[4]
        if data[5] != self._crc8(data[3:5]):
            return None, None

        return eco2, tvoc


    def get_eco2(self):
        eco2, _ = self.read()
        return eco2

    def get_tvoc(self):
        _, tvoc = self.read()
        return tvoc