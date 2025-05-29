from machine import I2C
import time

class MPU6050:
    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr
        self.i2c.writeto_mem(self.addr, 0x6B, b'\x00')  # Wake up sensor

    def read_accel(self):
        data = self.i2c.readfrom_mem(self.addr, 0x3B, 6)
        x = int.from_bytes(data[0:2], 'big', True)
        y = int.from_bytes(data[2:4], 'big', True)
        z = int.from_bytes(data[4:6], 'big', True)
        return {'x': x / 16384, 'y': y / 16384, 'z': z / 16384}

    def read_gyro(self):
        data = self.i2c.readfrom_mem(self.addr, 0x43, 6)
        x = int.from_bytes(data[0:2], 'big', True)
        y = int.from_bytes(data[2:4], 'big', True)
        z = int.from_bytes(data[4:6], 'big', True)
        return {'x': x / 131, 'y': y / 131, 'z': z / 131}
