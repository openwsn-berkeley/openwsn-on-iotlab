#!/usr/bin/python
import os
import sys

def syscall(cmd):
    print '>>> {0}'.format(cmd)
    os.system(cmd)
    
if len(sys.argv)>1:
    node = int(sys.argv[1])
else:
    node = 1
    
if syscall('ssh -o \"StrictHostKeyChecking no\" root@node-a8-{0} \'source /etc/profile; sudo pip install yappi openwsn-coap netifaces\''.format(node)) != 0:
    print "\nExample: python install.py <nodeId>\n"