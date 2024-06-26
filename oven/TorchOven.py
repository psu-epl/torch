'''
Created on Mar 1, 2013

@author: Pat Nystrom
'''
from __future__ import absolute_import
from __future__ import print_function
import serial
from . import modbus as M
from .crc16 import block_crc16 as modbus_crc16
import binascii
from struct import pack, unpack, error as struct_error
import time

# Register definitions
import oven.regs as regs

class TorchOven(object):
    def __init__(self, port=0):
        self.sp = serial.Serial(port, baudrate=9600, timeout=0.5)
        self.fmt = M.Formatter(addr=2)
        self.started = False

    def cksum_msg(self, cmd):
        return cmd+pack('>H', modbus_crc16(cmd))

    def write_reg(self, reg, value):
        time.sleep(0.06)
        msg = self.cksum_msg(self.fmt.write_single_reg(reg, value))
        print('writing %.04x v=%d with cmd %s' % (reg, value, binascii.b2a_hex(msg)))
        self.sp.write(msg)
        resp = self.sp.read(6) # If this were standard MODBUS, it would be an 8-byte read
        return resp

    def read_regs(self, addr, count):
        ''' read count modbus regs starting at addr.
          return raw serial reply, including crc16 as last two bytes'''
        time.sleep(0.06)
        msg = self.cksum_msg(self.fmt.read_holding_regs(addr, count))
        print('reading reg %.04x with cmd %s' % (addr, binascii.b2a_hex(msg)), end="=")
        self.sp.flushInput()
        self.sp.write(msg)
        resp = self.sp.read(count*2 + 5)  # response has 2 byte header + 2 byte crc16, and 2 bytes per register
        rslt = unpack('>'+('H'*count), resp[3:-2])
        print("0x ", end='')
        for v in rslt:
            print(f"{v:02X}", end=' ')
        print("")
        return rslt

    def close(self):
        self.sp.close()

    def send_profile(self, profile):
        ''' profile is a list of 40 tuples (degrees_c, seconds)'''
        base = regs.PROFILE_BASE  # base of the profile table
        for p in profile:
            print('writing profile entry', hex(base))
            print(binascii.b2a_hex(self.write_reg(base, p[0])))
            print(binascii.b2a_hex(self.write_reg(base+2, p[1])))
            base += 4

    def init_sequence(self):
        print(self.read_regs(0x1004, 2))
        print(self.read_regs(0x1010, 2))
        print(self.read_regs(0x1014, 2))
        print(self.read_regs(0x1008, 3))

    def read_profile(self):
        return self.read_regs(regs.PROFILE_BASE, 80)

    def start(self):
        self.started = True
        self.write_reg(regs.RUNNING, 1)  

    def stop(self):
        self.started = False
        self.write_reg(regs.RUNNING, 0)  

    def read_temp(self):
        return self.read_regs(regs.CURRENT_TEMP, 1)[0]

class VirtualTorchOven(object):
    def __init__(self, port = 0):
        self.started = False

    def init_sequence(self):
        time.sleep(0.1)
        pass

    def send_profile(self, profile):
        self.profile = profile
        for line in profile:
            time.sleep(0.01)

    def read_profile(self):
        return self.profile

    def start(self):
        self.started = True
        self.start_time = time.time()

    def read_temp(self):
        time_decrementor = time.time() - self.start_time
        profile_index = 0
        while time_decrementor >= self.profile[profile_index][1]:
            if profile_index < len(self.profile)-1:
                time_decrementor -= self.profile[profile_index][1]
                profile_index += 1
            else:
                return self.profile[profile_index][0]
                break
        if profile_index == 0:
            last_temp = 15 # Room temperature, let's say
        else:
            last_temp = self.profile[profile_index-1][0]
        return int(last_temp + (time_decrementor/self.profile[profile_index][1])*(self.profile[profile_index][0] - last_temp))

    def stop(self):
        pass

    def close(self):
        pass

if __name__=='__main__':
    from serial.tools.list_ports import comports as comports
    ports = [cp[0] for cp in comports()]
    oven = TorchOven(ports[-1])
    '''
    start temp
    pre-soak 
    '''
    profile = DEFAULT_PROFILE
    try:
        oven.init_sequence()
        oven.send_profile(profile)
        oven.read_profile()
        oven.start()
        try:
            start = time.time()
            while (time.time() - start) < 30:
                try:
                    print("Temp: " + oven.read_temp())
                except struct_error as E:
                    print('Exception reading temp', str(E))
        finally:
            oven.stop()
    finally:
        oven.close()