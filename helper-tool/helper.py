import os
import subprocess
import threading
import argparse
import socket
import json
import signal
import time

from settings import *

class ReservationManagerException(Exception):
    def __init__(self,err=''):
        self.err  = err
    
    def __str__(self):
        return str(self.err)

class ReservationStopping(ReservationManagerException):
    def __str__(self):
        return '\nRESERVATION STOPPING: ' + ReservationManagerException.__str__(self)

class ReservationSelfStopping(ReservationManagerException):
    def __str__(self):
        return '\nRESERVATION SELF STOPPING: ' + ReservationManagerException.__str__(self)

class ReservationContinuing(ReservationManagerException):
    def __str__(self):
        return '\nRESERVATION CONTINUING: ' + ReservationManagerException.__str__(self)

class ExperimentTerminating(ReservationManagerException):
    def __str__(self):
        return '\nEXPERIMENT TERMINATING: ' + ReservationManagerException.__str__(self)

class ExperimentSelfTerminating(ReservationManagerException):
    def __str__(self):
        return '\nEXPERIMENT SELF TERMINATING: ' + ReservationManagerException.__str__(self)

class CommandError(ReservationManagerException):
    def __str__(self):
        return '\nCOMMAND ERROR: ' + ReservationManagerException.__str__(self)

class Reservation(threading.Thread):
    DUMPDIR                 = 'RESERVATIONS'
    STARTING                = '.STARTING'
    STOPPING                = '.STOPPING'
    ONGOING                 = '.ONGOING'
    RUNNING                 = '.RUNNING'
    TERMINATING             = '.TERMINATING'
    UPDATING                = '.UPDATING'
    MOTESAVAILABLE_PREAMBLE = 'motes_available'
    MOTESWORKING_PREAMBLE   = 'motes_working'
    MOTESSELECTED_PREAMBLE  = 'motes_selected'
    RESERVATION_GUARDTIME   = 600 # 10 minutes of guard time from the estimated end of the reservation
    
    def __init__(self,args,site):
        self.__args = args
        self.__site = site
        dict_start_functions = {
                        'start':        self.__reservation_start,
                        'stop':         self.__reservation_stop,
                        'run':          self.__openvisualizer_run,
                        'terminate':    self.__openvisualizer_terminate,
                        }
        dict_stop_functions = {
                        'start':        self.__reservation_stop,
                        'stop':         self.__dummy,
                        'run':          self.__openvisualizer_terminate,
                        'terminate':    self.__dummy,
                        }
        self.run = dict_start_functions[self.__args.command]
        self.stop = dict_stop_functions[self.__args.command]
        
        self.__working_directory    = os.getcwd()
        self.__dump_directory       = os.path.join(self.__working_directory,self.DUMPDIR)
        if not os.path.exists(self.__dump_directory):
            os.makedirs(self.__dump_directory)
        self.__file_firmware_regular    = os.path.join(self.__working_directory,'..','openwsn-fw',FW_REGULAR_PATH)
        self.__file_firmware_dagroot    = os.path.join(self.__working_directory,'..','openwsn-fw',FW_DAGROOT_PATH)
        self.__file_starting            = os.path.join(self.__working_directory,self.STARTING)
        self.__file_stopping            = os.path.join(self.__working_directory,self.STOPPING)
        self.__file_ongoing             = os.path.join(self.__working_directory,self.ONGOING)
        self.__file_running             = os.path.join(self.__working_directory,self.RUNNING)
        self.__file_terminating         = os.path.join(self.__working_directory,self.TERMINATING)
        self.__file_updating            = os.path.join(self.__working_directory,self.UPDATING)
        self.__reset_variables()
        self.__decide_ownership()
        threading.Thread.__init__(self)
    
    #-------------------self.run AND self.stop METHODS-------------------#
    
    def __reservation_start(self):
        
        # This method is called by a start command
        
        if not self.__ownership.is_set():
            return

        self.__set_starting()
        
        try:
            self.__update_openwsn()
            while True:
                try:
                    self.__reservation_start_body()
                except ReservationContinuing as e:
                    print e
                    # Exception raised to continue in trying another reservation in the cascade reservation process
                    self.__reservation_stop_body()
                else:
                    # The cascade reservation process is ok, so exit the loop
                    break
        except (ReservationStopping,ReservationSelfStopping,CommandError) as e:
            print e
            if not self.__is_stopping():
                self.__set_stopping()
        
        if self.__is_stopping():
            self.__clear_starting()
            self.__reservation_stop_body()
            self.__clear_stopping()
        else:
            self.__set_ongoing()
            self.__clear_starting()
        
    def __reservation_stop(self):
    
        # This method is called by a stop command or when pressing Ctrl-C when a start command is running 
        
        if not self.__is_stopping():
            if self.__is_running():
                self.__set_stopping()
                print 'STOP SIGNAL SENT TO THE RUNNING EXPERIMENT'
            elif self.__get_ongoing():
                print 'A RESERVATION IS ONGOING AND NO EXPERIMENT HAS BEEN DETECTED'
                self.__set_stopping()
                if self.__is_updating():
                    self.__clear_updating()
                self.__clear_ongoing()
                if self.__is_reservation_really_running():
                    self.__reservation_stop_body()
                self.__clear_stopping()
                print 'RESERVATION STOPPED'
            elif self.__is_starting():
                self.__set_stopping()
                print 'STOP SIGNAL SENT TO THE STARTING RESERVATION'        
            else:
                print 'NOTHING TO STOP'
        else:
            print 'ALREADY STOPPING THE ONGOING RESERVATION'
        if self.__is_starting() and not self.__ownership.is_set():
            self.__set_stopping()
            self.__clear_starting()
            self.__reservation_stop_body(force=True)
            self.__clear_stopping()
    
    def __openvisualizer_run(self):
        
        # This method is called by a run command
        
        if not self.__ownership.is_set():
            return
        
        self.__set_running()
        reservation_not_running = False
        try:
            if not self.__is_reservation_really_running():
                raise ReservationSelfStopping('No reservation running')
            else:
                time_remaining = self.__reservation_stopping_time - time.time()
                if (time_remaining) <= self.RESERVATION_GUARDTIME:
                    raise ReservationSelfStopping('Only {} minutes remaining within this reservation: not sufficient time'.format(time_remaining/60))
                print '{} minutes remaining within this reservation'.format(time_remaining/60)
            if self.__args.update:
                self.__update_openwsn()
                self.__set_updating()
            update = self.__is_updating()
            self.__openvisualizer_run_header(update)
            
            print '\nRunning openVisualizer'
            os.chdir(os.path.join(self.__working_directory,'..','openwsn-sw','software','openvisualizer','bin','openVisualizerApp'))
            command = ['python','openVisualizerWeb.py','--port',
                        '1234','--iotlabmotes',','.join([self.__convert_to_url(mote) for mote in self.__motes_selected])]
            self.__ownership.clear()
            s = subprocess.Popen(command, stdin = subprocess.PIPE, preexec_fn = preexec_function)
            while all([ s.poll()==None, 
                        not self.__is_terminating(),
                        not self.__is_stopping(),
                        (self.__reservation_stopping_time - time.time()) > self.RESERVATION_GUARDTIME,
                        ]):
                self.__ownership.wait(30)
                if self.__ownership.is_set():
                    break
            s.stdin.write('q\n')
            s.wait()
            time_remaining = self.__reservation_stopping_time - time.time()
            if self.__is_stopping():
                raise ReservationStopping('Reservation stopped while openVisualizer was running')
            elif time_remaining <= self.RESERVATION_GUARDTIME:
                raise ReservationSelfStopping('Only {} minutes remaining within this reservation: forced closing of openVisualizer'.format(time_remaining/60))
            elif self.__is_terminating():
                self.__clear_terminating()
                if self.__ownership.is_set():
                    print '\nCtrl-C forced closing openVisualizer'
                else:
                    self.__ownership.set()
                    print '\nAnother external process terminated the experiment: openVisualizer closed'
            else:
                print '\nOpenVisualizer gracefully stopped itself!'
            
            self.__openvisualizer_run_trailer(update)
            if self.__is_updating():
                self.__clear_updating()
        except (ExperimentTerminating,CommandError) as e:
            print e
            self.__set_updating()
        except (ExperimentSelfTerminating,ReservationStopping) as e:
            print e
        except ReservationSelfStopping as e:
            print e
            self.__set_stopping()
            reservation_not_running = True
        
        self.__clear_running()
        if self.__is_terminating():
            self.__clear_terminating()
        if self.__is_stopping():
            if self.__is_updating():
                self.__clear_updating()
            self.__clear_ongoing()
            if not reservation_not_running:
                self.__reservation_stop_body()
            self.__clear_stopping()
    
    def __openvisualizer_terminate(self):
        
        # This method is called by a terminate command or when pressing Ctrl-C when a run command is running
        
        if all([not self.__is_stopping(),self.__is_running()]):
            self.__set_terminating()
            self.__ownership.set()
            print 'TERMINATE SIGNAL SENT TO THE RUNNING EXPERIMENT'
        else:
            print 'NO EXPERIMENT TO TERMINATE OR THE RESERVATION IS STOPPING'
    
    def __dummy(self):
        pass
    
    #-------------------self.run AND self.stop HELPER METHODS-------------------#
    
    def __reservation_start_body(self):
        
        if not self.__args.moteAll:
            if self.__args.moteList:
                if len(self.__args.moteList) < self.__args.workingMotes:
                    raise ReservationSelfStopping('{} motes in moteList but at least {} must be working'.format(len(self.__args.moteList),self.__args.workingMotes))
            else:
                if self.__args.moteNumber < self.__args.workingMotes:
                    raise ReservationSelfStopping('{} motes required but at least {} must be working'.format(self.__args.moteNumber,self.__args.workingMotes))
                
        # Check motes availability
        command = ['experiment-cli','info','--site',self.__site,'-li']
        stdout = self.__run_command(command,'Before checking motes availability')
        motes_dict = json.loads(stdout)['items'][0][self.__site][MOTETYPE]
        if motes_dict.has_key('Alive'):
            self.__motes_alive = convert_string(motes_dict['Alive'])
        for state_motes in motes_dict.itervalues():
            self.__motes_all |= convert_string(state_motes)
        print '\n{} motes in total in {}:\n{}'.format(len(self.__motes_all),self.__site,convert_set(self.__motes_all))
        print '\n{} motes alive:\n{}'.format(len(self.__motes_alive),convert_set(self.__motes_alive))
        if self.__args.moteList:
            self.__motes_reserved = self.__motes_alive & self.__args.moteList
        elif self.__args.moteAll:
            self.__motes_reserved = self.__motes_alive.copy()
        else:
            self.__motes_reserved = self.__select_far_motes(self.__motes_alive,self.__args.moteNumber)
        if len(self.__motes_reserved) < self.__args.workingMotes:
            raise ReservationSelfStopping('{} motes to reserve but at least {} must be working'.format(len(self.__motes_reserved),self.__args.workingMotes))
        
        # Submit reservation
        command = ['experiment-cli','submit','-n',self.__args.name,'-d',self.__args.duration,
                    '-l','{},{},{},{}'.format(self.__site,MOTETYPE,convert_set(self.__motes_reserved),self.__file_firmware_regular)]
        stdout = self.__run_command(command,'Before submitting reservation')
        reservation_id = json.loads(stdout)['id']
        self.__set_reservation_id(reservation_id)
        print '\n{} motes reserved:\n{}'.format(len(self.__motes_reserved),convert_set(self.__motes_reserved))
        
        # Wait for reservation running
        command = ['experiment-cli','wait','-i','{}'.format(reservation_id)]
        stdout = self.__run_command(command,'Before waiting Running state')
        
        # Get information to compute the reservation stopping time
        command = ['experiment-cli','get','-l','--state','Running']
        stdout = self.__run_command(command,'Before getting information about the reservation stopping time')
        reservation_stopping_time = None
        for reservation in json.loads(stdout)['items']:
            if int(reservation['id']) == reservation_id:
                reservation_stopping_time = float(reservation['date']) + float(reservation['duration'])
        if reservation_stopping_time == None:
            raise ReservationSelfStopping('Not able to compute the reservation stopping time')
        self.__set_reservation_stopping_time(reservation_stopping_time)
        print '\nTemporary Reservation ID {}'.format(self.__reservation_id)
        print 'Reservation stopping in {} minutes'.format((self.__reservation_stopping_time-time.time())/60)
        
        # Check reservation
        command = ['experiment-cli','get','-p','-i','{}'.format(self.__reservation_id)]
        stdout = self.__run_command(command,'Before checking reservation')
        motes_dict = json.loads(stdout)['deploymentresults']
        if motes_dict.has_key('0'):
            self.__motes_available = set([self.__convert_to_id(mote) for mote in motes_dict['0']])
        if len(self.__motes_available) < self.__args.workingMotes:
            raise ReservationContinuing('{} motes available but at least {} must be working'.format(len(self.__motes_available),self.__args.workingMotes))
        print '\n{} motes available:\n{}'.format(len(self.__motes_available),convert_set(self.__motes_available))
        
        # Log to file
        with open(self.__file_motes_available,'w') as f:
            f.write('#ALL {}\n'.format(convert_set(self.__motes_all)))
            f.write('#ALIVE {}\n'.format(convert_set(self.__motes_alive)))
            f.write('#RESERVED {}\n'.format(convert_set(self.__motes_reserved)))
            f.write('#AVAILABLE {}\n'.format(convert_set(self.__motes_available)))
        
        # Select those motes passing some tests
        motes_stopped           = self.__send_node_cli_command_to_motes(self.__motes_available,'stop')
        motes_started           = self.__send_node_cli_command_to_motes(motes_stopped,'start')
        motes_updated           = self.__send_node_cli_command_to_motes(motes_started,'update',self.__file_firmware_regular)
        motes_reset             = self.__send_node_cli_command_to_motes(motes_updated,'reset')
        motes_reachable         = self.__get_motes_reachable(motes_reset,time_to_test=600)
        motes_stopped_again     = self.__send_node_cli_command_to_motes(self.__motes_available,'stop')
        self.__motes_working    = motes_reachable & motes_stopped_again
        if len(self.__motes_working) < self.__args.workingMotes:
            raise ReservationContinuing('{} motes working but at least {} must be working'.format(len(self.__motes_working),self.__args.workingMotes))
        print '\n{} motes working:\n{}'.format(len(self.__motes_working),convert_set(self.__motes_working))
        
        # Log to file and exit
        with open(self.__file_motes_working,'w') as f:
            f.write('#WORKING {}\n'.format(convert_set(self.__motes_available)))
            f.write('#START_STOPPED {}\n'.format(convert_set(motes_stopped)))
            f.write('#START_STARTED {}\n'.format(convert_set(motes_started)))
            f.write('#START_UPDATED {}\n'.format(convert_set(motes_updated)))
            f.write('#START_RESET {}\n'.format(convert_set(motes_reset)))
            f.write('#START_REACHABLE {}\n'.format(convert_set(motes_reachable)))
            f.write('#START_STOPPEDAGAIN {}\n'.format(convert_set(motes_stopped_again)))
            if self.__motes_available - motes_stopped_again:
                f.write('#START_POSSIBLYNOTSTOPPED {}\n'.format(convert_set(self.__motes_available - motes_stopped_again)))
            f.write('#WORKING {}\n'.format(convert_set(self.__motes_working)))
        print '\nReservation ID {}'.format(self.__reservation_id)
    
    def __reservation_stop_body(self,force=False):
        
        if self.__reservation_id:
            command = ['experiment-cli','stop','-i','{}'.format(self.__reservation_id)]
            self.__run_command(command)
            command = ['experiment-cli','wait','-i','{}'.format(self.__reservation_id),'--state','Error,Terminated']
            self.__run_command(command)
            self.__reset_variables()
        elif force:
            command = ['experiment-cli','stop']
            self.__run_command(command)
    
    def __openvisualizer_run_header(self,update):
        
        select_again = False
        if update:
            motes_not_working = self.__motes_working - \
                                self.__send_node_cli_command_to_motes(self.__motes_working,'stop')
            if motes_not_working:
                with open(self.__file_motes_working,'a') as f:
                    f.write('#BEFORERUN_POSSIBLYNOTSTOPPED {}\n'.format(convert_set(motes_not_working)))
                self.__motes_working -= motes_not_working
                with open(self.__file_motes_working,'a') as f:
                    f.write('#WORKING {}\n'.format(convert_set(self.__motes_working)))
                select_again = True
        
        while len(self.__motes_working) >= self.__args.numMotes:
            if select_again:
                self.__select_motes_to_run()
            motes_to_test = self.__motes_selected.copy()
            motes_not_working = set([])
            dagroot_was_updated = False
            update_dagroot = True
            while motes_to_test:
                motes_not_working = motes_to_test - \
                                    self.__send_node_cli_command_to_motes(motes_to_test,'start')
                if motes_not_working:
                    with open(self.__file_motes_working,'a') as f:
                        f.write('#BEFORERUN_NOTSTARTED {}\n'.format(convert_set(motes_not_working)))
                    break
                if update:
                    motes_not_working = motes_to_test - self.__dagroot - \
                                        self.__send_node_cli_command_to_motes(motes_to_test - self.__dagroot,'update',self.__file_firmware_regular)
                    if motes_not_working:
                        with open(self.__file_motes_working,'a') as f:
                            f.write('#BEFORERUN_NOTUPDATED {}\n'.format(convert_set(motes_not_working)))
                        break
                if not dagroot_was_updated or update_dagroot:
                    update_dagroot = False
                    motes_not_working = self.__dagroot - \
                                        self.__send_node_cli_command_to_motes(self.__dagroot,'update',self.__file_firmware_dagroot)
                    dagroot_was_updated = not motes_not_working
                    if motes_not_working:
                        with open(self.__file_motes_working,'a') as f:
                            f.write('#BEFORERUN_DAGROOTNOTUPDATED {}\n'.format(convert_set(motes_not_working)))
                        break
                motes_not_working = motes_to_test - \
                                    self.__send_node_cli_command_to_motes(motes_to_test,'reset')
                if motes_not_working:
                    with open(self.__file_motes_working,'a') as f:
                        f.write('#BEFORERUN_NOTRESET {}\n'.format(convert_set(motes_not_working)))
                    break
                motes_not_working = motes_to_test - \
                                    self.__get_motes_reachable(motes_to_test)
                if motes_not_working:
                    if motes_to_test - motes_not_working:
                        motes_to_test = motes_not_working.copy()
                        update = True
                        if self.__dagroot & motes_to_test:
                            update_dagroot = True
                        continue
                    else:
                        with open(self.__file_motes_working,'a') as f:
                            f.write('#BEFORERUN_NOTREACHABLE {}\n'.format(convert_set(motes_not_working)))
                        break
                return
            self.__motes_working -= motes_not_working
            if dagroot_was_updated:
                motes_not_working = self.__dagroot - \
                                    self.__send_node_cli_command_to_motes(self.__dagroot,'update',self.__file_firmware_regular)
                if motes_not_working:
                    with open(self.__file_motes_working,'a') as f:
                        f.write('#BEFORERUN_DAGROOTNOTUPDATEDBACK {}\n'.format(convert_set(motes_not_working)))
                    self.__motes_working -= motes_not_working
            motes_not_working = self.__motes_selected - \
                                self.__send_node_cli_command_to_motes(self.__motes_selected,'stop')
            if motes_not_working:
                with open(self.__file_motes_working,'a') as f:
                    f.write('#BEFORERUN_POSSIBLYNOTSTOPPED {}\n'.format(convert_set(motes_not_working)))
            self.__motes_working -= motes_not_working
            select_again = True
            with open(self.__file_motes_working,'a') as f:
                f.write('#WORKING {}\n'.format(convert_set(self.__motes_working)))
        raise ExperimentSelfTerminating('{} motes working but at least {} must be working'.format(len(self.__motes_working),self.__args.numMotes))
    
    def __openvisualizer_run_trailer(self,update):
        
        with open(self.__file_motes_selected,'a') as f:
            f.write('#SELECTED {}\n'.format(convert_set(self.__motes_selected)))
            f.write('#DAGROOT {}\n'.format(convert_set(self.__dagroot)))
        if update:
            motes_not_started = self.__motes_working - self.__send_node_cli_command_to_motes(self.__motes_working,'start')
            dagroot_not_started = set([])
            motes_not_updated = self.__motes_working - self.__send_node_cli_command_to_motes(self.__motes_working,'update',self.__file_firmware_regular)
            dagroot_not_updated = set([])
            motes_not_stopped = self.__motes_working - self.__send_node_cli_command_to_motes(self.__motes_working,'stop')
        else:
            motes_not_started = set([])
            dagroot_not_started = self.__dagroot - self.__send_node_cli_command_to_motes(self.__dagroot,'start')
            motes_not_updated = set([])
            dagroot_not_updated = self.__dagroot - self.__send_node_cli_command_to_motes(self.__dagroot,'update',self.__file_firmware_regular)
            motes_not_stopped = self.__motes_selected - self.__send_node_cli_command_to_motes(self.__motes_selected,'stop')
        
        motes_not_working = set([])
        with open(self.__file_motes_working,'a') as f:
            if motes_not_started:
                motes_not_working |= motes_not_started
                f.write('#AFTERRUN_NOTSTARTED {}\n'.format(convert_set(motes_not_started)))
            if dagroot_not_started:
                motes_not_working |= dagroot_not_started
                f.write('#AFTERRUN_DAGROOTNOTSTARTED {}\n'.format(convert_set(dagroot_not_started)))
            if motes_not_updated:
                motes_not_working |= motes_not_updated
                f.write('#AFTERRUN_NOTUPDATED {}\n'.format(convert_set(motes_not_updated)))
            if dagroot_not_updated:
                motes_not_working |= dagroot_not_updated
                f.write('#AFTERRUN_DAGROOTNOTUPDATEDBACK {}\n'.format(convert_set(dagroot_not_updated)))
            if motes_not_stopped:
                motes_not_working |= motes_not_stopped
                f.write('#AFTERRUN_POSSIBLYNOTSTOPPED {}\n'.format(convert_set(motes_not_stopped)))
        self.__motes_working -= motes_not_working
        if motes_not_working:
            with open(self.__file_motes_working,'a') as f:
                f.write('#WORKING {}\n'.format(convert_set(self.__motes_working)))
        
    def __update_openwsn(self):
        
        os.chdir(os.path.join(self.__working_directory,'..','openwsn-fw'))
        
        # pull openwsn-fw
        command = ['git','pull']
        self.__run_command(command,'Before pulling openwsn-fw')
        
        # compile dagroot
        command = ['scons','board=wsn430v14','toolchain=mspgcc','noadaptivesync=1','dagroot=1','oos_openwsn']
        self.__run_command(command,'Before compiling dagroot firmware')
        
        # create filenames for dagroot and regular: if the path is the same, change the dagroot firmware file name
        if self.__file_firmware_dagroot == self.__file_firmware_regular:
            self.__file_firmware_dagroot = os.path.join(os.path.split(self.__file_firmware_dagroot)[0],'03oos_openwsn_dagroot_prog.ihex')
            os.rename(self.__file_firmware_regular,self.__file_firmware_dagroot)
        
        command = ['scons','board=wsn430v14','toolchain=mspgcc','noadaptivesync=1','oos_openwsn']
        self.__run_command(command,'Before compiling regular firmware')
        
        os.chdir(os.path.join(self.__working_directory,'..','openwsn-sw'))
        
        command = ['git','pull']
        self.__run_command(command,'Before pulling openwsn-sw')
        
    def __is_reservation_really_running(self):
        
        command = ['experiment-cli','get','-i','{}'.format(self.__reservation_id),'-s']
        stdout = self.__run_command(command)
        reservation_state = json.loads(stdout)['state']
        
        return reservation_state == 'Running'
        
    #-------------------UTILITY METHODS-------------------#
        
    def __send_node_cli_command_to_motes(self,motes,op,op_arg=None):
        motes_successful = set([])
        if motes:
            command = ['node-cli','-i','{}'.format(self.__reservation_id),
                        '-l','{},{},{}'.format(self.__site,MOTETYPE,convert_set(motes)),'--{}'.format(op)]
            if op_arg:
                command += [op_arg]
            stdout = self.__run_command(command,'Before node-cli command')
            motes_dict = json.loads(stdout)
            if motes_dict.has_key('0'):
                motes_successful = set([self.__convert_to_id(mote) for mote in motes_dict['0']])
            if motes-motes_successful:
                print '{} motes not working ({}):\n{}'.format(len(motes-motes_successful),op,convert_set(motes-motes_successful))
        return motes_successful
    
    def __loop_send_node_cli_command_to_motes(self,motes,op,op_arg=None):
        motes_failure = motes - self.__send_node_cli_command_to_motes(motes,op,op_arg)
        while motes_failure:
            motes_failure -= self.__send_node_cli_command_to_motes(motes_failure,op,op_arg)
        
    def __get_motes_reachable(self,motes_to_test,timeout_read=10,time_to_test=20):
        motes_responding = set([])
        error_message = 'While checking reachability'
        if motes_to_test:
            print '\nChecking TCP reachability for:\n{}'.format(convert_set(motes_to_test))
            motes = dict([(mote,TestReachability(self.__convert_to_url(mote),timeout_read)) for mote in motes_to_test])
            for mote_thread in motes.itervalues():
                mote_thread.start()
            while time_to_test>0:
                time.sleep(timeout_read)
                if self.__is_stopping():
                    for mote_thread in motes.itervalues():
                        mote_thread.stop()
                    for mote_thread in motes.itervalues():
                        mote_thread.join()
                    raise ReservationStopping(error_message)
                if self.__is_terminating():
                    for mote_thread in motes.itervalues():
                        mote_thread.stop()
                    for mote_thread in motes.itervalues():
                        mote_thread.join()
                    raise ExperimentTerminating(error_message)
                time_to_test -= timeout_read
            for mote_thread in motes.itervalues():
                mote_thread.stop()
            for mote_thread in motes.itervalues():
                mote_thread.join()
            for mote,mote_thread in motes.iteritems():
                if mote_thread.get_response():
                    motes_responding.add(mote)
        if motes_to_test-motes_responding:
            print '{} motes not working (tcp):\n{}'.format(len(motes_to_test-motes_responding),convert_set(motes_to_test-motes_responding))
        return motes_responding
    
    def __run_command(self,input,check_message=''):
        if check_message:
            if self.__is_stopping():
                raise ReservationStopping(check_message)
            if self.__is_terminating():
                raise ExperimentTerminating(check_message)
        print '\n'+' '.join(input)
        s = subprocess.Popen(input,stdout=subprocess.PIPE,stderr=subprocess.PIPE,preexec_fn = preexec_function)
        stdout,stderr = s.communicate()
        if stderr and not stdout:
           raise CommandError(stderr)
        return stdout
    
    def __select_motes_to_run(self):
        self.__motes_selected.clear()
        if self.__args.closeFlag:
            self.__motes_selected = set(sorted(self.__motes_working)[:self.__args.numMotes])
        else:
            self.__motes_selected = self.__select_far_motes(self.__motes_working,self.__args.numMotes)
        motes_selected_sorted = sorted(self.__motes_selected)
        if self.__args.dagrootCentered:
            self.__dagroot = set([motes_selected_sorted[len(motes_selected_sorted)/2]])
        else:
            self.__dagroot = set([motes_selected_sorted[0]])
        
    def __select_far_motes(self,motes,numMotes):
        motes_sorted = sorted(motes)
        motes_selected = set([])
        factor=float(len(motes)-1)/float(numMotes-1)
        factor_diff=0
        while motes_sorted:
            motes_selected.add(motes_sorted.pop(0))
            factor_int = int(factor + factor_diff)
            factor_diff = factor + factor_diff - factor_int
            motes_sorted = motes_sorted[factor_int-1:]
        return motes_selected
        
    def __convert_to_id(self,mote_url):
        return int(mote_url.split('.')[0].split('-')[1])
    
    def __convert_to_url(self,mote_id):
        return '{}-{}.{}.iot-lab.info'.format(MOTETYPE,mote_id,self.__site)
    
    #-------------------STATE METHODS-------------------#
    
    def __decide_ownership(self):
        self.__ownership = threading.Event()
        if self.__args.command == 'start':
            if self.__get_ongoing():
                print 'RESERVATION RUNNING: YOU CANNOT START ANOTHER ONE!'
                return
            if self.__is_starting():
                print 'RESERVATION STARTING: YOU CANNOT START ANOTHER ONE!'
                return
            if self.__is_stopping():
                print 'RESERVATION STOPPING: WAIT!'
                return
            self.__ownership.set()
        elif self.__args.command == 'run':
            if self.__is_stopping():
                print 'RESERVATION STOPPING: TRY RESTARTING FIRST A RESERVATION!'
                return
            if self.__is_starting():
                print 'RESERVATION STARTING: WAIT!'
                return
            if not self.__get_ongoing():
                print 'NO RESERVATION PRESENT: START A RESERVATION BEFORE RUNNING OPENWSN!'
                return
            if self.__is_running() or self.__is_terminating():
                print 'OPENVISUALIZER RUNNING: YOU CANNOT RUN ANOTHER OPENVISUALIZER PROCESS!'
                return
            with open(self.__file_motes_working) as f:
                lines = f.readlines()
            for line in lines:
                tag, motes = line.strip().split()
                motes_set = convert_string(motes)
                if tag == '#WORKING':
                    self.__motes_working = motes_set
            if len(self.__motes_working)<self.__args.numMotes:
                print 'NO SUFFICIENT MOTES: YOU CANNOT RUN SO MANY MOTES IN THIS RESERVATION!'
                return
            newMotesSelectedList = not os.path.isfile(self.__file_motes_selected)
            if not newMotesSelectedList:
                with open(self.__file_motes_selected) as f:
                    lines = f.readlines()
                for line in lines:
                    tag, motes = line.strip().split()
                    motes_set = convert_string(motes)
                    if tag == '#SELECTED':
                        self.__motes_selected = motes_set
                    elif tag == '#DAGROOT':
                        self.__dagroot = motes_set
                if self.__motes_selected - self.__motes_working:
                    newMotesSelectedList = True
            if newMotesSelectedList:
                self.__select_motes_to_run()
            self.__ownership.set()
        
    def __reset_variables(self):
        self.__motes_all = set([])
        self.__motes_alive = set([])
        self.__motes_reserved = set([])
        self.__motes_available = set([])
        self.__motes_working = set([])
        self.__motes_selected = set([])
        self.__dagroot = set([])
        self.__set_reservation_id()
        
    def __set_reservation_id(self,reservation_id = None):
        self.__reservation_id = reservation_id
        self.__file_motes_available = None
        self.__file_motes_working = None
        self.__file_motes_selected = None
        if reservation_id:
            self.__file_motes_available = os.path.join(self.__dump_directory,self.MOTESAVAILABLE_PREAMBLE+'_{}.txt'.format(reservation_id))
            self.__file_motes_working = os.path.join(self.__dump_directory,self.MOTESWORKING_PREAMBLE+'_{}.txt'.format(reservation_id))
            if all(k in self.__args.__dict__ for k in ('numMotes','closeFlag','dagrootCentered')):
                density = 'far'
                if self.__args.closeFlag:
                    density = 'close'
                dagroot_position = 'side'
                if self.__args.dagrootCentered:
                    dagroot_position = 'center'
                self.__file_motes_selected = os.path.join(self.__dump_directory,
                            self.MOTESSELECTED_PREAMBLE+'_{}_{}_{}_{}_dagroot.txt'.format(reservation_id,self.__args.numMotes,density,dagroot_position))
                        
    def __set_reservation_stopping_time(self,reservation_stopping_time):
        self.__reservation_stopping_time = reservation_stopping_time
    
    def __is_starting(self):
        return os.path.isfile(self.__file_starting)
    
    def __set_starting(self):
        with open(self.__file_starting,'w') as f:
            f.write('')
        
    def __clear_starting(self):
        os.remove(self.__file_starting)
    
    def __is_stopping(self):
        return os.path.isfile(self.__file_stopping)
    
    def __set_stopping(self):
        with open(self.__file_stopping,'w') as f:
            f.write('')
        
    def __clear_stopping(self):
        os.remove(self.__file_stopping)
    
    def __get_ongoing(self):
        toReturn = os.path.isfile(self.__file_ongoing)
        if toReturn:
            reservation_id = None
            reservation_stopping_time = None
            with open(self.__file_ongoing) as f:
                lines = f.readlines()
                for line in lines:
                    tag, value = line.strip().split()
                    if tag == '#RESERVATIONID':
                        reservation_id = int(value)
                    elif tag == '#RESERVATIONSTOPPINGTIME':
                        reservation_stopping_time = float(value)
            self.__set_reservation_id(reservation_id)
            self.__set_reservation_stopping_time(reservation_stopping_time)
        return toReturn
    
    def __set_ongoing(self):
        with open(self.__file_ongoing,'w') as f:
            f.write('#RESERVATIONID {}\n'.format(self.__reservation_id))
            f.write('#RESERVATIONSTOPPINGTIME {}\n'.format(self.__reservation_stopping_time))
        
    def __clear_ongoing(self):
        os.remove(self.__file_ongoing)
    
    def __is_running(self):
        return os.path.isfile(self.__file_running)
    
    def __set_running(self):
        with open(self.__file_running,'w') as f:
            f.write('')
        
    def __clear_running(self):
        os.remove(self.__file_running)
    
    def __is_terminating(self):
        return os.path.isfile(self.__file_terminating)
    
    def __set_terminating(self):
        with open(self.__file_terminating,'w') as f:
            f.write('')
        
    def __clear_terminating(self):
        os.remove(self.__file_terminating)
    
    def __is_updating(self):
        return os.path.isfile(self.__file_updating)
    
    def __set_updating(self):
        with open(self.__file_updating,'w') as f:
            f.write('')
        
    def __clear_updating(self):
        os.remove(self.__file_updating)
    
class TestReachability(threading.Thread):
    def __init__(self, mote,timeout):
        self.__mote = mote
        self.__sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.__sock.settimeout(timeout)
        self.__event = threading.Event()
        self.__event.set()
        self.__response = True
        threading.Thread.__init__(self)
    
    def run(self):
        try:
            self.__sock.connect((self.__mote,20000))
            while self.__event.isSet():
                try:
                    data = self.__sock.recv(1024)
                except socket.timeout:
                    self.__response = False
        except:
            self.__response = False
        self.__sock.close()
    
    def stop(self):
        self.__event.clear()
    
    def get_response(self):
        return self.__response
    
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
    
    subparsers = parser.add_subparsers()
    
    # start parser
    start_parser = subparsers.add_parser('start', help='start reservation')
    
    start_parser.add_argument('-n', '--name',
                        default     = 'minimaltest',
                        help        = 'experiment name',
                        )
    
    start_parser.add_argument('-d', '--duration',
                        default     = '1440',
                        help        = 'experiment duration in minutes',
                        )
    
    start_parser.add_argument('-w', '--workingMotes',
                        type        = int,
                        default     = 2,
                        help        = 'minimum number of working motes',
                        )
    
    group_start = start_parser.add_mutually_exclusive_group()
    
    group_start.add_argument('-ml','--moteList',
                        action      = MoteListAction,
                        default     = set([]),
                        help        = 'select specific motes',
                        )
    
    group_start.add_argument('-ma','--moteAll',
                        action      = 'store_true',
                        default     = False,
                        help        = 'select all motes',
                        )
    
    group_start.add_argument('-mn','--moteNumber',
                        type        = int,
                        default     = 20,
                        help        = 'select a number of motes',
                        )
    
    start_parser.set_defaults(command = 'start')
    
    # stop parser
    stop_parser = subparsers.add_parser('stop', help='stop reservation')
    
    stop_parser.add_argument('--force',
                        action      = 'store_true',
                        default     = False,
                        help        = 'force any reservation to stop',
                        )
    
    stop_parser.set_defaults(command = 'stop')
    
    # run parser
    run_parser = subparsers.add_parser('run', help='run openVisualizer')
    
    run_parser.add_argument('-u','--update',
                        action      = 'store_true',
                        default     = False,
                        help        = 'update to the latest version of OpenWSN',
                        )
    
    run_parser.add_argument('-r', '--dagrootCentered',
                        action      = 'store_true',
                        default     = False,
                        help        = 'dagroot in the middle (default at the border)',
                        )
    
    group_run = run_parser.add_mutually_exclusive_group()
    
    group_run.add_argument('-f','--farMotes',
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
    
    run_parser.set_defaults(closeFlag = False, numMotes = 10, command = 'run')
    
    # terminate parser
    terminate_parser = subparsers.add_parser('terminate', help='terminate openVisualizer')
    
    terminate_parser.set_defaults(command = 'terminate')
    
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

def preexec_function():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def main():
    args = parse_options()
    s = subprocess.Popen('hostname',stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    stdout,_ = s.communicate()
    site = stdout.strip()
    r = Reservation(args,site)
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
