'''
Created on Mar 1, 2013

@author: Pat Nystrom
'''
import serial
import modbus as M
from crc16 import block_crc16 as modbus_crc16
import binascii
from struct import pack, unpack

class TorchOven(object):
    def __init__(self, port=0):
        self.sp = serial.Serial(port, baudrate=9600)
        self.sp.setTimeout(0.5)
        self.fmt = M.Formatter(addr=2)
            
    def cksum_msg(self, cmd):
        return cmd+pack('>H', modbus_crc16(cmd))
        
    
    def write_reg(self, reg, value):
        print 'writing', reg, value
        msg = self.cksum_msg(self.fmt.write_multiple_regs(reg, [value]))
        print binascii.b2a_hex(msg) 
        self.sp.write(msg)
        resp = self.sp.read(8)
        print binascii.b2a_hex(resp)
    
    def read_regs(self, addr, count):
        ''' read count modbus regs starting at addr.
          return raw serial reply, including crc16 as last two bytes'''
        msg = self.cksum_msg(self.fmt.read_holding_regs(addr, count))
        self.sp.write(msg)
        return self.sp.read(count*2 + 4)  # response has 2 byte header + 2 byte crc16, and 2 bytes per register
            
    def close(self):
        self.sp.close()
        
if __name__=='__main__':
    # create an oven comm object on com1 (0th comm port)
    oven = TorchOven(0)
    try:
        print binascii.b2a_hex(oven.read_regs(0x1004, 2))
    finally:
        oven.close()