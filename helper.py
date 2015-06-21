import os
import subprocess
import threading
import argparse
import socket
import json

MOTETYPE            = 'wsn430'
MOTENAMEPREAMBLE    = MOTETYPE + '-'
FW                  = '~/openwsn/openwsn-fw/build/wsn430v14_mspgcc/projects/common/03oos_openwsn_prog.ihex'
FW_DAGROOT          = '~/openwsn/openwsn-fw/build/wsn430v14_mspgcc_dagroot/projects/common/03oos_openwsn_prog.ihex'
MOTESCHECKED        = 'motes_checked'
MOTELIST            = 'mote_list.txt'
DUMPDIR             = 'RESERVATIONS'
STARTINGRESERVATION = '.STARTING'
RUNNINGRESERVATION  = '.RUNNING'
STOPPINGRESERVATION = '.STOPPING'

NUMBERMOTES         = 100

class MoteListAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, convert_string(values))

class MoteFarAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        setattr(namespace, 'closeFlag', False)

class MoteCloseAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        setattr(namespace, 'closeFlag', True)

def parse_options():
    
    # main parser
    parser = argparse.ArgumentParser()
    
    parser.add_argument('-s','--site',
                        default     = 'rennes',
                        help        = 'select site',
                        )
    
    subparsers = parser.add_subparsers()
    
    # start parser
    start_parser = subparsers.add_parser('start', help='start reservation')
    
    start_parser.add_argument('-l','--moteList',
                        action      = MoteListAction,
                        default     = set([]),
                        help        = 'select specific motes'
                        )
    
    start_parser.add_argument('-n', '--name',
                        default     = 'minimaltest',
                        help        = 'experiment name',
                        )
    
    start_parser.add_argument('-d', '--duration',
                        default     = '1440',
                        help        = 'experiment duration in minutes',
                        )
    
    start_parser.set_defaults(command = 'start')
    
    # stop parser
    stop_parser = subparsers.add_parser('stop', help='stop reservation')
    
    stop_parser.set_defaults(command = 'stop')
    
    # run parser
    run_parser = subparsers.add_parser('run', help='run openVisualizer')
    
    group_run = run_parser.add_mutually_exclusive_group()
    
    group_run.add_argument( '-f','--farMotes',
                        type        = int,
                        dest        = 'numMotes',
                        action      = MoteFarAction,
                        help        = 'motes are selected as far as possible',
                        )
    
    group_run.add_argument('-c', '--closeMotes',
                        type        = int,
                        dest        = 'numMotes',
                        action      = MoteCloseAction,
                        help        = 'motes are selected as close as possible',
                        )
    
    group_run.add_argument('-p', '--previousMoteList',
                        action      = 'store_true',
                        default     = False,
                        help        = 'motes are selected based on the last working set',
                        )
    
    run_parser.set_defaults(closeFlag = False, numMotes = 30, command = 'run')
    
    args = parser.parse_args()
    
    return args

def convert_string(motesString):
    temp = [range(int(group.split('-')[0]),int(group.split('-')[-1])+1) for group in motesString.split('+')]
    setToReturn = set(reduce(lambda x,y:x+y,temp))
    return setToReturn

def convert_set(motesSet):
    temp = sorted(motesSet)
    stringToReturn = ''
    if temp:
        current = temp.pop(0)
        stringToReturn += str(current)
        previous = current
        group = False
    while temp:
        current = temp.pop(0)
        if current - previous == 1:
            group = True
            if not temp:
                stringToReturn += '-' + str(current)
        else:
            if group:
                stringToReturn += '-' + str(previous)
            stringToReturn += '+' + str(current)
            group = False
        previous = current
    return stringToReturn

# def prepare_openwsn():
    # print ''
    # print '+--------------------------------------+'
    # print '|         Preparing OpenWSN            |'
    # print '+--------------------------------------+'
    # print ''
    # os.chdir(os.path.join('..','openwsn-fw'))
    # subprocess.call(['git','pull'])
    # subprocess.call(['scons','board=wsn430v14','toolchain=mspgcc','noadaptivesync=1','oos_openwsn'])
    # subprocess.call(['scons','board=wsn430v14','toolchain=mspgcc','noadaptivesync=1','dagroot=1','oos_openwsn'])
    # os.chdir(os.path.join('..','openwsn-sw'))
    # subprocess.call(['git','pull'])
    # subprocess.call(['git','clean','-fX'])
    # os.chdir(os.path.join('..','scripts-iotlab'))
    
# def run(args):
    # return
    # motes_to_reserve = []
    # if args.moteList:
        # if len(set(args.moteList).intersection(motes_available)) == len():
            # pass
    # print args.moteList
    # if len(motes_available) >= args.numMotes:
        # if args.closeFlag:
            # motes_to_reserve = motes_available[:args.numMotes]
        # else:
            # motes_to_reserve = []
            # factor=float(len(motes_available)-1)/float(args.numMotes-1)
            # factor_diff=0
            # i=0
            # while i<len(motes_available):
                # motes_to_reserve += [motes_available[i]]
                # factor_int = int(factor + factor_diff)
                # factor_diff = factor + factor_diff - factor_int
                # i += factor_int-1
    # else:
        # print 'Mote number cannot be reserved at this time'
        # return
    
# def select_motes(args, motes_available):
    # print
    # print '+--------------------------------------+'
    # print '|           Selecting motes            |'
    # print '+--------------------------------------+'
    # print
    
    # return motes
  
# def run_Openvisualizer():
    # global motes_reserved
    # print
    # print '+--------------------------------------+'
    # print '|       running Openvisualizer         |'
    # print '+--------------------------------------+'
    # print
    # os.chdir(os.path.join('..','openwsn-sw','software','openvisualizer','bin','openVisualizerApp'))
    # subprocess.call(['python','openVisualizerWeb.py','--port','1234','--iotlabmotes',','.join([MOTENAMEPREAMBLE+str(mote) for mote in motes_reserved])])
    
# def main2():
    
    # # prepare OpenWSN
    # #prepare_openwsn()
    
    # # parse options
    # args = parse_options()
    
    # motes_not_reliable = []
    # if not args.eraseHistory:
        # # load motes not reliable
        # if os.path.isfile(MOTESNOTRELIABLE):
            # with open(MOTESNOTRELIABLE) as f:
                # motes_not_reliable += [int(mote) for mote in f.readline().strip().split(' ')]
    # else:
        # # reset file (in case, motes not reliable will be appended later)
        # f = open(MOTESNOTRELIABLE,'w')
        # f.close()
    
    # # check which motes are available
    # motes_available = check_available_motes(args)
    
    # # start reservation
    # reservation_id = start_reservation(args,motes_available,motes_not_reliable)
    
    # while True:
        
        # if reservation_id is None:
            
            # # stop here if there are not sufficient motes
            # return
        
        # # check reservation
        # new_motes_not_reliable = check_reservation(reservation_id)
        
        # if not new_motes_not_reliable:
            
            # # motes correctly flashed and working: exit this loop and run openvisualizer
            # break
        # else:
            
            # # store new not reliable motes found 
            # with open(MOTESNOTRELIABLE,'a') as f:
                # f.write(' '.join([str(mote) for mote in new_motes_not_reliable]))
            
            # # update overall set of not reliable motes
            # motes_not_reliable += new_motes_not_reliable
            
            # # stop reservation
            # stop_reservation(reservation_id)
            
            # # check which motes are available
            # motes_available = check_available_motes(args)
            
            # #start reservation excluding motes not reliable
            # reservation_id = start_reservation(args,motes_available,motes_not_reliable)
        
    # # run Openvisualizer
    # run_Openvisualizer()
    
    # # stop reservation
    # stop_reservation(reservation_id)

class ReservationError(Exception):
    def __init__(self,code,err=''):
        self.code = code
        self.err  = err
    
class Reservation(threading.Thread):
    def __init__(self,args):
        self.__args = args
        dict_start_functions = {
                        'start':    self.__start_reservation,
                        'stop':     self.__stop_reservation,
                        'run':      self.__start_openvisualizer,
                        }
        dict_stop_functions = {
                        'start':    self.__stop_reservation,
                        'stop':     self.__dummy,
                        'run':      self.__stop_openvisualizer,
                        }
        self.__start_command = dict_start_functions[self.__args.command]
        self.__stop_command = dict_stop_functions[self.__args.command]
        self.__reset_variables()
        threading.Thread.__init__(self)
    
    def run(self):
        self.__start_command()
    
    def stop(self):
        self.__stop_command()
    
    def __start_reservation(self):
        # This method is called by a start process
        if not (self.__get_running() or self.__is_starting() or self.__is_stopping()):
            self.__set_starting()
            condition = True 
            while condition:
                try:
                    self.__start_internal()
                except ReservationError as e:
                    print '{}: {}'.format(e.code, e.err)
                    if e.code not in ['STOPPING','TRY AGAIN']:
                        self.__set_stopping()
                    if e.code != 'TRY AGAIN':
                        self.__clear_starting()
                    self.__stop_internal()
                    if e.code != 'TRY AGAIN':
                        self.__clear_stopping()
                        condition = False
                else:
                    self.__set_running()
                    self.__clear_starting()
                    condition = False
    
    def __stop_reservation(self):
        # This method is called by a stop process
        if not self.__is_stopping():
            if self.__get_running():
                self.__set_stopping()
                self.__clear_running()
                self.__stop_internal()
                self.__clear_stopping()
            elif self.__is_starting():
                self.__set_stopping()
    
    def __dummy(self):
        pass
    
    def __start_openvisualizer(self):
        if not self.__get_running():
            print 'START RESERVATION BEFORE RUNNING OPENVISUALIZER'
            return
        
        with open(DUMPDIR+'/'+MOTESCHECKED+'_{}.txt'.format(self.__reservation_id)) as f:
            lines = f.readlines()
        
        for line in lines:
            tag, motes = line.strip().split()
            motes_set = convert_string(motes)
            if tag == '#ALL':
                self.__motes_all = motes_set
            elif tag == '#ALIVE':
                self.__motes_alive = motes_set
            elif tag == '#AVAILABLE':
                self.__motes_available = motes_set
            elif tag == '#WORKING':
                self.__motes_working = motes_set
            elif tag == '#SELECTED':
                if self.__args.previousMoteList:
                    self.__motes_selected = motes_set
            elif tag == '#DAGROOT':
                if self.__args.previousMoteList:
                    self.__dagroot = motes_set
        
        # if args.all:
            # motes = motes_available
        # elif args.list:
            # motes = list(set(args.moteList).intersection(motes_available))
        # elif len(motes_available) >= args.numMotes:
            # if args.closeFlag:
                # motes = motes_available[:args.numMotes]
            # else:
                # factor=float(len(motes_alive)-1)/float(args.numMotes-1)
                # factor_diff=0
                # while motes_alive:
                    # motes_reserved += [motes_alive.pop(0)]
                    # factor_int = int(factor + factor_diff)
                    # factor_diff = factor + factor_diff - factor_int
                    # for i in xrange(factor_int-1):
                        # if motes_alive:
                            # motes_alive.pop(0)
        # else:
            # motes = None
    
    def __stop_openvisualizer(self):
        pass
    
    def __start_internal(self):
        # Check motes availability
        command = ['experiment-cli','info','--site',self.__args.site,'-li']
        stdout,stderr = self.__run_command(command,'Before checking motes availability',check_stderr=True)
        motes_dict = json.loads(stdout)['items'][0][self.__args.site][MOTETYPE]
        if motes_dict.has_key('Alive'):
            self.__motes_alive = convert_string(motes_dict['Alive'])
        for state_motes in motes_dict.itervalues():
            self.__motes_all |= convert_string(state_motes)
        if self.__args.moteList:
            self.__motes_alive &= self.__args.moteList
            self.__motes_all   &= self.__args.moteList
        print '{} MOTES IN {}'.format(len(self.__motes_all),self.__args.site)
        print
        if self.__motes_alive < NUMBERMOTES:
            raise ReservationError('DO NOT TRY AGAIN','NOT SUFFICIENT MOTES ALIVE: {}'.format(len(self.__motes_alive)))
        print '{} MOTES ALIVE'.format(len(self.__motes_alive))
        print convert_set(self.__motes_alive)
        print
        
        # Submit reservation
        command = ['experiment-cli','submit','-n',self.__args.name,'-d',self.__args.duration,
                    '-l','{},{},{},{}'.format(self.__args.site,MOTETYPE,convert_set(self.__motes_alive),FW)]
        stdout,stderr = self.__run_command(command,'Before submitting reservation',check_stderr=True)
        self.__reservation_id = json.loads(stdout)['id']
        print 'RESERVATION ID {}'.format(self.__reservation_id)
        
        # Wait for reservation running
        command = ['experiment-cli','wait','-i','{}'.format(self.__reservation_id)]
        stdout,stderr = self.__run_command(command,'Before waiting Running state')
        print stderr
        print stdout
        
        # Log to file
        if not os.path.exists(DUMPDIR):
            os.makedirs(DUMPDIR)
        with open(DUMPDIR+'/'+MOTESCHECKED+'_{}.txt'.format(self.__reservation_id),'a') as f:
            f.write('#ALL {}\n'.format(convert_set(self.__motes_all)))
            f.write('#ALIVE {}\n'.format(convert_set(self.__motes_alive)))
        
        # Check reservation
        command = ['experiment-cli','get','-p','-i','{}'.format(self.__reservation_id)]
        stdout,stderr = self.__run_command(command,'Before checking reservation',check_stderr=True)
        motes_dict = json.loads(stdout)['deploymentresults']
        if motes_dict.has_key('0'):
            self.__motes_available = set([int(mote.split('.')[0][len(MOTENAMEPREAMBLE):]) for mote in motes_dict['0']])
        if self.__motes_available < NUMBERMOTES:
            raise ReservationError('TRY AGAIN','NOT SUFFICIENT MOTES AVAILABLE: {}'.format(self.__motes_available))
        print '{} MOTES AVAILABLE'.format(len(self.__motes_available))
        print convert_set(self.__motes_available)
        print
        
        # Log to file
        if not os.path.exists(DUMPDIR):
            os.makedirs(DUMPDIR)
        with open(DUMPDIR+'/'+MOTESCHECKED+'_{}.txt'.format(self.__reservation_id),'a') as f:
            f.write('#AVAILABLE {}\n'.format(convert_set(self.__motes_available)))
        
        # Check if motes are reachable and in case reflash them
        self.__motes_working = self.__get_motes_reachable(self.__motes_available)
        motes_to_reflash = self.__motes_available - self.__motes_working
        while motes_to_reflash:
            motes_reflashed = self.__update_motes(motes_to_reflash)
            self.__motes_working |= self.__get_motes_reachable(motes_reflashed)
            if self.__motes_working & motes_to_reflash:
                motes_to_reflash -= self.__motes_working
            else:
                motes_to_reflash = set([])
        self.__motes_working = self.__get_motes_reachable(self.__motes_working)
        if self.__motes_working < NUMBERMOTES:
            raise ReservationError('TRY AGAIN','NOT SUFFICIENT MOTES WORKING: {}'.format(self.__motes_working))
        print '{} MOTES WORKING'.format(len(self.__motes_working))
        print convert_set(self.__motes_working)
        print
        
        # Log to file
        with open(DUMPDIR+'/'+MOTESCHECKED+'_{}.txt'.format(self.__reservation_id),'a') as f:
            f.write('#WORKING {}\n'.format(convert_set(self.__motes_working)))
    
    def __get_motes_reachable(self,motes_to_test):
        motes_responding = set([])
        for mote_n in motes_to_test:
            mote = MOTENAMEPREAMBLE+str(mote_n)
            sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            sock.connect((mote,20000))
            sock.settimeout(20)
            try:
                data = sock.recv(1024)
            except socket.timeout:
                print '{} not working'.format(mote)
            else:
                motes_responding.add(mote_n)
            sock.close()
        return motes_responding
    
    def __update_motes(self,motes_to_flash,firmware=FW):
        motes_flashed = set([])
        if motes_to_flash:
            command = ['node-cli','-up',firmware,
                        '-l','{},{},{}'.format(self.__args.site,MOTETYPE,convert_set(motes_to_flash))]
            stdout,stderr = self.__run_command(command,'Before updating motes',check_stderr=True)
            motes_dict = json.loads(stdout)
            if motes_dict.has_key('0'):
                motes_flashed = set([int(mote.split('.')[0][len(MOTENAMEPREAMBLE):]) for mote in motes_dict['0']])
                motes_flashed |= self.__update_motes(motes_to_flash - motes_flashed,firmware)
        return motes_flashed
    
    def __stop_internal(self):
        if self.__reservation_id:
            command = ['experiment-cli','stop','-i','{}'.format(self.__reservation_id)]
            self.__run_command(command)
            command = ['experiment-cli','wait','-i','{}'.format(self.__reservation_id),'--state','Error,Terminated']
            self.__run_command(command)
            self.__reset_variables()
    
    def __reset_variables(self):
        self.__motes_all = set([])
        self.__motes_alive = set([])
        self.__motes_available = set([])
        self.__motes_working = set([])
        self.__motes_selected = set([])
        self.__motes_dagroot = set([])
        self.__reservation_id = None
    
    def __is_starting(self):
        return os.path.isfile(STARTINGRESERVATION+self.__args.site)
    
    def __set_starting(self):
        with open(STARTINGRESERVATION+self.__args.site,'w') as f:
            f.write('')
    
    def __clear_starting(self):
        os.remove(STARTINGRESERVATION+self.__args.site)
    
    def __get_running(self):
        toReturn = os.path.isfile(RUNNINGRESERVATION+self.__args.site)
        if toReturn:
            with open(RUNNINGRESERVATION+self.__args.site) as f:
                self.__reservation_id = int(f.readline())
        return toReturn
    
    def __set_running(self):
        with open(RUNNINGRESERVATION+self.__args.site,'w') as f:
            f.write('{}'.format(self.__reservation_id))
    
    def __clear_running(self):
        os.remove(RUNNINGRESERVATION+self.__args.site)
    
    def __is_stopping(self):
        return os.path.isfile(STOPPINGRESERVATION+self.__args.site)
    
    def __set_stopping(self):
        with open(STOPPINGRESERVATION+self.__args.site,'w') as f:
            f.write('')
    
    def __clear_stopping(self):
        os.remove(STOPPINGRESERVATION+self.__args.site)
    
    def __run_command(self,input,stopping_check_message='',check_stderr=False):
        if stopping_check_message:
            if self.__is_stopping():
                raise ReservationError('STOPPING',stopping_check_message)
        s = subprocess.Popen(input,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout,stderr = s.communicate()
        if check_stderr:
            if stderr:
                raise ReservationError('STDERR',stderr)
        return stdout,stderr

def main():
    args = parse_options()
    r = Reservation(args)
    r.start()
    try:
        while r.isAlive():
            r.join(1000)
    except KeyboardInterrupt:
        r.stop()
    if r.isAlive():
        r.join()
    
#============================ main ============================================

if __name__=="__main__":
    main()