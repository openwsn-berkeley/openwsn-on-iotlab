#!/usr/bin/python
import os
import sys
import socket
import time

def syscall(cmd):
    print '>>> {0}'.format(cmd)
    os.system(cmd)

def main():
    target = socket.gethostname()+'.log'
    targetstate = os.stat(target)
    lastmodified = targetstate.st_mtime
    
    while True: 
        newtime = os.stat(target).st_mtime
        if newtime == lastmodified:
            syscall("flash_a8_m3 /home/root/A8/03oos_openwsn_prog.exe")
        else:
            time.sleep(30)
        lastmodified = newtime
    

if __name__ == '__main__':
    main()
    

            