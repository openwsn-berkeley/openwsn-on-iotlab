#!/usr/bin/python
import os
import sys

def syscall(cmd):
    print '>>> {0}'.format(cmd)
    os.system(cmd)
    
if len(sys.argv)>1:
    (d,l) = (int(sys.argv[1]),int(sys.argv[2]))
else:
    print "e.g: exp_submit.py (duration) (numberOfNodes)\n"
    raise TypeError("Wrong parameters!\n")
    
syscall('experiment-cli submit -d {0} -l {1},archi=a8:at86rf231+site=saclay'.format(d,l)) 