#!/usr/bin/python
import sys
import getopt
import os
import threading
import time

# =========================== variable ========================================

successNode   = []
failedNode    = []
commandList   = {
'flash'     :'flash_a8_m3 A8/03oos_openwsn_prog.exe',
'moteprobe' :'cd ~/A8/experiment/; python moteProbe.py &',
'killpython':'killall python',
'watchdog'  :'cd ~/A8/experiment/; python watchdog.py &',
'runrover'  :'cd ~/A8/openwsn-sw/software/openvisualizer/bin/openVisualizerApp/; python openRoverApp.py &',
'flashdagroot'     :'flash_a8_m3 A8/03oos_openwsn_prog_dagroot.exe'
}

# =========================== functions =======================================

def syscall(cmd):
    print '>>> {0}'.format(cmd)
    return os.system(cmd)

def usage():
    output = "issue commands to multiple nodes\n"
    output += "issue_command.py -c <command> -s <startNodeId> -e <endNoteId> -d <dagrootId>\n"
    output += "==== shortCMD = real command ====\n"
    output += "---- flash      flash_a8_m3 A8/03oos_openwsn_prog.exe\n"
    output += "---- moteprobe  cd ~/A8/serialData/; python moteProbe.py &\n"
    output += "---- killpython killall python\n"
    output += "---- watchdog   cd ~/A8/experiment/; python watchdog.py &\n"
    output += "---- runrover   cd ~/A8/openwsn-sw/software/openvisualizer/bin/openVisualizerApp/; python openRoverApp.py &\n"
    output += "(you also can type the command directly)\n"
    print output
    
# record command result in to file
def record(cmd,start,end, list_node):
    with open('{0}.log'.format(cmd),'a') as f:
        f.write("\n")
        # ==== statistic
        f.write("==== Flashing statistic result ====\n")
        if list_node is None:
            f.write("Try to flash {0} nodes:\n".format(end-start))
        else:
            f.write("Try to flash {0} nodes:\n".format(len(list_node.split(','))))
        f.write("Success: {0} Failed: {1}\n".format(len(successNode),len(failedNode)))
        # ==== successful node list
        nodelist = ""
        for i in range(len(successNode)):
            nodelist += "{0},".format(successNode[i])
        f.write("---Success List---\n")
        f.write(nodelist+'\n')

        # ==== failed node list
        nodelist = ""
        for i in range(len(failedNode)):
            nodelist += "{0},".format(failedNode[i])
        f.write("---failed List---\n")
        f.write(nodelist+'\n')
        timestampe = [i for i in time.localtime()]
        f.write("recorded at {0}/{1} {2}:{3}:{4}\n".format(timestampe[1],timestampe[2],timestampe[3],timestampe[4],timestampe[5],))

# =========================== class ===========================================
        
class multipleNodeCommand(threading.Thread):

    def __init__(self,id,command, dagroot):
    
        self.id        = id
        self.isdagroot = (id == dagroot)
        self.status    = False
        self.command   = command
        
        if command in commandList:
            self.command_desc = commandList[command]
        else:
            self.command_desc = command
        
        self.goOn = True
        
        # initialize the parent class
        threading.Thread.__init__(self)
        
        self.start()
# =========================== thread ==========================================
    def run(self):
        
        if self.command == 'flash' and self.isdagroot:
            if syscall("ssh -n -f -o \"StrictHostKeyChecking no\" root@node-a8-{0} 'source /etc/profile; {1}'\n".format(self.id,commandList['flashdagroot'])) == 0:
                self.status = True
        else:
            if self.command == 'runrover':
                # kill the port first in case it's in use.
                syscall("ssh -n -f -o \"StrictHostKeyChecking no\" root@node-a8-{0} 'source /etc/profile; kill -9 $(lsof -t -i:5683)'".format(self.id))
            if syscall("ssh -n -f -o \"StrictHostKeyChecking no\" root@node-a8-{0} 'source /etc/profile; {1}'\n".format(self.id,self.command_desc)) == 0:
                self.status = True
        
        self.goOn = False
            
    def getId(self):
        return self.id
        
    def getStatus(self):
        return self.status
        
    def getgoOn(self):
        return self.goOn

# =========================== main ============================================
def main():
    
    # get options
    cmd,start,end,dagroot,nodelist = None, None, None, None, None
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'c:s:e:d:l:h', ['cmd=', 'start=', 'end=', 'list=', 'dagroot=', 'help'])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
        
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(2)
        elif opt in ('-c', '--cmd'):
            cmd = arg
        elif opt in ('-s', '--start'):
            start = int(arg)
        elif opt in ('-e', '--end'):
            end = int(arg)
        elif opt in ('-d', '--dagroot'):
            dagroot = int(arg)
        elif opt in ('-l', '--list'):
            nodelist = arg
        else:
            usage()
            sys.exit(2)
        
    # check valid fo options
    if nodelist == None and (cmd == None or start == None):
        usage()
        sys.exit(2)
    elif end is None and nodelist is None:
        end = start + 1
        
    # start jobs
    list_backup = nodelist
    if list_backup is None:
        nodelist = [multipleNodeCommand(i,cmd, dagroot) for i in range(start,end)]
    else:
        nodelist = [multipleNodeCommand(i,cmd, dagroot) for i in [int(i) for i in nodelist.split(',')]]
    for node in nodelist:
        id = node.getId()
        while node.getgoOn():
            pass
        if node.getStatus():
            successNode.append(id)
        else:
            failedNode.append(id)
    
    # record command result
    record(cmd,start,end, list_backup)
        


# ==== start from here
if __name__ == '__main__':
    main()