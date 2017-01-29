#!/usr/bin/python
import os
import sys
import socket
import time
import re

def syscall(cmd):
    print '>>> {0}'.format(cmd)
    os.system(cmd)
    
def isSync():
    with open(socket.gethostname()+'.log','r') as f:
        s=f.read()
        m=re.search('[\S\s]*(~S\S\S{0}{1}\S\S~)[\S\s]*'.format(chr(0),chr(1)),s)
        if m:
            return True
        else:
            return False

def main():
    target = socket.gethostname()+'.log'
    targetstate = os.stat(target)
    lastmodified = targetstate.st_mtime
    time.sleep(30)
    while True: 
        newtime = os.stat(target).st_mtime
        if newtime == lastmodified:
            if isSync()==False:
                syscall("flash_a8_m3 /home/root/A8/03oos_openwsn_prog.exe")
            else:
                break
        else:
            time.sleep(30)
        lastmodified = newtime
    

if __name__ == '__main__':
    main()
    

            