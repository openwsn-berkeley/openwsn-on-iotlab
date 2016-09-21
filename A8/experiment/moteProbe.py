#!/usr/bin/python
import os

import glob
import platform
import threading

import serial
import socket
import time
import sys

import OpenHdlc

#============================ functions =======================================


def findSerialPorts():
    '''
    Returns the serial ports of the motes connected to the computer.
    
    :returns: A list of tuples (name,baudrate) where:
        - name is a strings representing a serial port, e.g. 'COM1'
        - baudrate is an int representing the baurate, e.g. 115200
    '''
    if os.name=='posix':
        if platform.system() == 'Darwin':
            portMask = ['/dev/tty.usbserial-*']
        else:
            portMask = ['/dev/ttyUSB*', '/dev/ttyAMA*']
        serialports = ["/dev/ttyA8_M3", 500000]
    
    return serialports

#============================ class ===========================================

class moteProbe(threading.Thread):
    
    MODE_SERIAL    = 'serial'
    MODE_EMULATED  = 'emulated'
    MODE_IOTLAB    = 'IoT-LAB'
    MODE_ALL       = [
        MODE_SERIAL,
        MODE_EMULATED,
        MODE_IOTLAB,
    ]
    
    def __init__(self,serialport=None):
        
        # verify params
        if   serialport:
            self.mode = self.MODE_SERIAL
        else:
            raise SystemError()
        
        # store params
        if   self.mode==self.MODE_SERIAL:
            self.serialport       = serialport[0]
            self.baudrate         = serialport[1]
            self.portname         = self.serialport
        else:
            raise SystemError()
        
        # log
        print "creating moteProbe attaching to {0}".format(
                self.portname,
            )
        
        # local variables
        self.hdlc                 = OpenHdlc.OpenHdlc()
        self.lastRxByte           = self.hdlc.HDLC_FLAG
        self.busyReceiving        = False
        self.inputBuf             = ''
        self.outputBuf            = []
        self.outputBufLock        = threading.RLock()
        self.dataLock             = threading.Lock()
        # flag to permit exit from read loop
        self.goOn                 = True
        
        # initialize the parent class
        threading.Thread.__init__(self)
        
        # give this thread a name
        self.name                 = 'moteProbe@'+self.portname
        
        if self.mode in [self.MODE_EMULATED,self.MODE_IOTLAB]:
            # Non-daemonized moteProbe does not consistently die on close(),
            # so ensure moteProbe does not persist.
            self.daemon           = True
    
        # start myself
        self.start()
    
    #======================== thread ==========================================
    
    def run(self):
        try:
            # log
            print "start running"
        
            while self.goOn:     # open serial port
                
                # log 
                print "open port {0}".format(self.portname)
                
                if   self.mode==self.MODE_SERIAL:
                    self.serial = serial.Serial(self.serialport,self.baudrate)
                    self.serial.setDTR(0)
                    self.serial.setRTS(0)
                else:
                    raise SystemError()
                
                while self.goOn: # read bytes from serial port
                    try:
                        if   self.mode==self.MODE_SERIAL:
                            rxBytes = self.serial.read(1)
                        elif self.mode==self.MODE_EMULATED:
                            rxBytes = self.serial.read()
                        elif self.mode==self.MODE_IOTLAB:
                            rxBytes = self.serial.recv(1024)
                        else:
                            raise SystemError()
                    except Exception as err:
                        print err
                        log.warning(err)
                        time.sleep(1)
                        break
                    else:
                        for rxByte in rxBytes:
                            if      (
                                        (not self.busyReceiving)             and 
                                        self.lastRxByte==self.hdlc.HDLC_FLAG and
                                        rxByte!=self.hdlc.HDLC_FLAG
                                    ):
                                # start of frame
                                self.busyReceiving       = True
                                self.inputBuf            = self.hdlc.HDLC_FLAG
                                self.inputBuf           += rxByte
                            elif    (
                                        self.busyReceiving                   and
                                        rxByte!=self.hdlc.HDLC_FLAG
                                    ):
                                # middle of frame
                                
                                self.inputBuf           += rxByte
                            elif    (
                                        self.busyReceiving                   and
                                        rxByte==self.hdlc.HDLC_FLAG
                                    ):
                                # end of frame
                                self.busyReceiving       = False
                                self.inputBuf           += rxByte
                                
                                if self.inputBuf[1]=='R':
                                    with self.outputBufLock:
                                        if self.outputBuf:
                                            outputToWrite = self.outputBuf.pop(0)
                                            self.serial.write(outputToWrite)
                                else:
                                    with open(socket.gethostname()+'.log','a') as f:
                                        f.write(self.inputBuf)
                        
                            self.lastRxByte = rxByte
                        
        except Exception as err:
            print self.name,err
            sys.exit(-1)
    
    #======================== public ==========================================
    
    def getPortName(self):
        with self.dataLock:
            return self.portname
    
    def getSerialPortBaudrate(self):
        with self.dataLock:
            return self.baudrate
    
    def close(self):
        self.goOn = False
    
    #======================== private =========================================
    
    def _bufferDataToSend(self,data):
        
        # frame with HDLC
        hdlcData = self.hdlc.hdlcify(data)
        
        # add to outputBuf
        with self.outputBufLock:
            self.outputBuf += [hdlcData]
         
def main():
    mote = moteProbe(findSerialPorts())
    
         
if __name__ == "__main__":
    main()