#!/usr/bin/python
import os
import sys

def syscall(cmd):
    print '>>> {0}'.format(cmd)
    os.system(cmd)
    
if len(sys.argv)>1:
    (nodeId,port) = (int(sys.argv[1]),int(sys.argv[2]))
else:
    print "e.g: python runov.py <nodeId> <port>\n"
    raise TypeError("Wrong parameters!\n")

command = 'cd ~/A8/openwsn-sw/software/openvisualizer/; sudo scons runweb --port {0}'.format(port)
syscall('ssh -o \"StrictHostKeyChecking no\" -L {0}:localhost:{0} root@node-a8-{1} \'source /etc/profile; {2}\''.format(port, nodeId, command))