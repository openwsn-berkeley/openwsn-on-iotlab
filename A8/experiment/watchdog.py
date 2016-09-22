#!/usr/bin/python
import os
import sys
import socket
import time

def syscall(cmd):
    print '>>> {0}'.format(cmd)
    os.system(cmd)

resetError = "\nBOARD_RESET!\n"

def getPid(command):
    returnVal = None
    syscall("ps | grep python > {0}".format(socket.gethostname()+'.info'))
    with open(socket.gethostname()+'.info','r') as f:
        for line in f:
            list =  line.split()
            if command in list:
                returnVal = list[0]
                break
    syscall("rm {0}".format(socket.gethostname()+'.info'))
    return returnVal

def main():
    target = socket.gethostname()+'.log'
    targetstate = os.stat(target)
    lastmodified = targetstate.st_mtime
    
    while True: 
        newtime = os.stat(target).st_mtime
        if newtime == lastmodified:
            Pid = getPid('moteProbe.py')
            if Pid != None:
                syscall("kill -9 {0}".format(Pid))
            else:
                raise TypeError("No moteProbe.py running!\n")
            syscall("flash_a8_m3 /home/root/A8/03oos_openwsn_prog.exe")
            with open(target,'a') as f:
                f.write(resetError)
            syscall("cd ~/A8/experiment/; python moteProbe.py &")
        else:
            time.sleep(30)
        lastmodified = newtime
    

if __name__ == '__main__':
    main()
    

            