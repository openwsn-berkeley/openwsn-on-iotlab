#!/usr/bin/python
import time
import traceback
import StackDefines
import pprint
import ast
import os

#============================ defines =========================================

CELLTYPE_OFF              = 0
CELLTYPE_TX               = 1
CELLTYPE_RX               = 2
CELLTYPE_TXRX             = 3

SLOTFRAME_LENGTH          = 101

#============================ class ===========================================
class LogfileAnalyzer(object):
    
    def __init__(self,logfilePath):

        self.errorcount     = {}
        self.scheduletable  = {}
        self.syncTime       = {}
        self.firstCellTime  = {}
        self.cellUsage      = {}
        self.cellPDR        = {}
        self.moteAddress    = {}
        self.neighbortable  = {}
        self.timeCorrection = {}
        self.logfilePath    = logfilePath
        
        # analyze
        self.analyzeAllFiles()
        
        # write result to files
        if not (os.path.exists(os.path.dirname(self.logfilePath+'analyzeResult/'))):
            os.makedirs(os.path.dirname(self.logfilePath+'analyzeResult/'))
        with open('{0}analyzeResult/errors.txt'.format(self.logfilePath),'w') as f:
            f.write(str(self.errorcount))
        self.writeToFile('{0}analyzeResult/cells_vs_rank.txt'.format(self.logfilePath),self.scheduletable)
        self.writeToFile('{0}analyzeResult/timeCorrection.txt'.format(self.logfilePath),self.timeCorrection)
        self.writeToFile('{0}analyzeResult/networkSyncTime.txt'.format(self.logfilePath),self.syncTime)
        self.writeToFile('{0}analyzeResult/firstCellTime.txt'.format(self.logfilePath),self.firstCellTime) 
        self.writeToFile('{0}analyzeResult/cellUsage.txt'.format(self.logfilePath),self.cellUsage)
        self.writeToFile('{0}analyzeResult/cell_pdr.txt'.format(self.logfilePath),self.cellPDR)
        self.writeToFile('{0}analyzeResult/isNoResNeigbor.txt'.format(self.logfilePath),self.neighbortable)
        self.writeToFile('{0}analyzeResult/moteId.txt'.format(self.logfilePath),self.moteAddress)
    
    def analyzeAllFiles(self):
        for filename in os.listdir(self.logfilePath):
            if filename.endswith('.parsed'):
                print 'Analyzing {0}...'.format(filename),
                self.analyzeOneFile(self.logfilePath+filename)
                print 'done.'

    def analyzeOneFile(self,filename):
        with open(filename,'r') as f:
            oneFileData = []
            for line in f:
                oneFileData += [ast.literal_eval(line)]
            
        # ==== how many errors?
        for d in oneFileData:
            if 'errcode' in d:
                errstring = StackDefines.errorDescriptions[d['errcode']]
                if d['errcode'] == 60:
                    rc,sm = StackDefines.sixtop_returncode[d['arg1']],StackDefines.sixtop_statemachine[d['arg2']]
                    errstring = errstring.format(rc,sm)
                if errstring not in self.errorcount:
                    self.errorcount[errstring] = 0
                self.errorcount[errstring] += 1
        
        # ==== schedule vs rank
        self.scheduletable[filename] = {}
        for d in oneFileData:
            if 'slotOffset' in d:
                self.scheduletable[filename][d['row']] = d
            if 'myDAGrank' in d:
                self.scheduletable[filename]['myDAGrank']= d
                
        # ==== timeCorrection
        self.timeCorrection[filename] = {}
        haveTxCell = False
        for d in oneFileData:
            if 'minCorrection' in d:
                self.timeCorrection[filename]['timeCorrection'] = d
            if 'myDAGrank' in d:
                self.timeCorrection[filename]['myDAGrank']= d
            if 'slotOffset' in d and d['type'] == CELLTYPE_TX:
                haveTxCell = True
            if 'errcode' in d and d['errcode']==26 and haveTxCell==True:
                # after mote has Tx cell, stop recording if mote got de-sync'ed
                break
        
        # ==== network sync Time
        self.syncTime[filename] = {}
        isSynced = False
        for d in oneFileData:
            if 'isSync' in d and d['isSync'] == 1:
                isSynced = True
            if isSynced is True and 'asn_0_1' in d and ('row' in d) is False:
                    self.syncTime[filename] = d
                    break 
                    
        # ==== first cell installed time
        self.firstCellTime[filename] = {}
        isFirstCell = False
        for d in oneFileData:
            if 'slotOffset' in d and d['type'] == CELLTYPE_TX: 
                isFirstCell = True
            if isFirstCell is True and 'myDAGrank' in d:
                self.firstCellTime[filename]['myDAGrank']= d
                if 'asn_0_1' in self.firstCellTime[filename].keys():
                    break
            if isFirstCell is True and 'asn_0_1' in d and ('row' in d) is False:
                self.firstCellTime[filename]['asn_0_1'] = d
                if 'myDAGrank' in self.firstCellTime[filename].keys():
                    break
                    
        # ==== usage of sixop reserved cells
        self.cellUsage[filename] = []
        slotFrameCount         = 0
        cellusagePerSlotFrame  = 0
        cellPerSlotframe       = 0
        for d in oneFileData:
            if 'slotOffset' in d:
                if d['type'] == CELLTYPE_OFF:
                    continue
                if d['slotOffset'] == 0 and d['type'] == CELLTYPE_TXRX:
                    self.cellUsage[filename] += [(slotFrameCount,cellusagePerSlotFrame,cellPerSlotframe)]
                    cellusagePerSlotFrame   = 0
                    cellPerSlotframe        = 0
                    slotFrameCount         += 1
                    continue
                if d['type'] == CELLTYPE_TX:
                    cellusagePerSlotFrame += countOneInBinary(d['usageBitMap'])
                    cellPerSlotframe      += 1
        
        # ==== PDR statistic of sixtop reserved cells
        self.cellPDR[filename] = {}
        for d in oneFileData:
            if 'slotOffset' in d:
                if d['type'] == CELLTYPE_TX:
                    if d['numTx'] != 0:
                        self.cellPDR[filename]['{0} {1}'.format(d['slotOffset'],d['channelOffset'])] = float(d['numTxACK'])/float(d['numTx'])
                        
        # ==== last neighbor table
        self.neighbortable[filename] = {}
        for d in oneFileData:
            if 'isNoRes' in d:
                self.neighbortable[filename][d['row']] = d
        
        # ==== mote mapping
        self.moteAddress[filename] = {}
        for d in oneFileData:
            if 'my16bID' in d:
                self.moteAddress[filename]['my16bID'] = hex(d['my16bID'])

    def writeToFile(self,filename,data):
        with open(filename,'w') as f:
            pp = pprint.PrettyPrinter(indent=4)
            f.write(pp.pformat(data))
    

#============================ main ============================================

def main():
    try:
        LogfileAnalyzer(LOGFILE_PATH)
        raw_input("Script ended normally. Press Enter to close.")
    except Exception as err:
        print traceback.print_exc()
        raw_input("Script CRASHED. Press Enter to close.")

#============================ helper ==========================================

def countOneInBinary(number):
    count = 0
    while (number>0):
        count   = count+1;
        number  = number & (number-1);
        
    return count
        
if __name__ == "__main__":
    main()
