#!/usr/bin/python
import struct
import os
import time
from collections import namedtuple
import sys
sys.path.append(os.path.abspath('../experiment'))
import OpenHdlc
import traceback
import StackDefines
import pprint

#============================ defines =========================================
LOGFILE_PATH              = '52838/'

CELLTYPE_OFF              = 0
CELLTYPE_TX               = 1
CELLTYPE_RX               = 2
CELLTYPE_TXRX             = 3

SLOTFRAME_LENGTH          = 101


#============================ class ===========================================
class fieldParsingKey(object):
    def __init__(self,length,val,name,structure,fields):
        self.length      = length
        self.val        = val
        self.name       = name
        self.structure  = structure
        self.fields     = fields

class getFigureData(object):
    def __init__():
        self.scheduletable  = {}
        self.syncTime       = {}
        self.cellUsage      = {}
        self.cellPDR        = {}

class LogfileParser(object):
    
    HDLC_FLAG              = '\x7e'
    HDLC_FLAG_ESCAPED      = '\x5e'
    HDLC_ESCAPE            = '\x7d'
    HDLC_ESCAPE_ESCAPED    = '\x5d'
    
    def __init__(self):

        self.scheduletable  = {}
        self.syncTime       = {}
        self.cellUsage      = {}
        self.cellPDR        = {}
        self.moteAddress    = {}
        # parse
        self.parseAllFiles()

    # get figure data
    def getFigure1Data(self,moteid,oneFileData):
        self.scheduletable[moteid] = {}
        for d in oneFileData:
            if 'slotOffset' in d:
                self.scheduletable[moteid][d['row']] = d
            if 'myDAGrank' in d:
                self.scheduletable[moteid]['myDAGrank']= d
    def getFigure2Data(self,moteid,oneFileData):
        self.syncTime[moteid] = {}
        isSynced = False
        for d in oneFileData:
            if 'isSync' in d and d['isSync'] == 1:
                isSynced = True
            if isSynced is True and 'asn_0_1' in d and ('row' in d) is False:
                    self.syncTime[moteid] = d
                    break    
    def getFigure3Data(self,moteid,oneFileData):
        self.cellUsage[moteid] = []
        for d in oneFileData:
            if 'slotOffset' in d:
                if d['type'] == CELLTYPE_TX:
                    self.cellUsage[moteid] += [(d['slotOffset'],countOneInBinary(d['usageBitMap']))]

    def getFigure4Data(self,moteid,oneFileData):
        self.cellPDR[moteid] = [0 for i in range(SLOTFRAME_LENGTH)]
        for d in oneFileData:
            if 'slotOffset' in d:
                if d['type'] == CELLTYPE_TX:
                    if d['numTx'] != 0:
                        self.cellPDR[moteid][d['slotOffset']] = float(d['numTxACK'])/float(d['numTx'])

    def getMoteAddress(self,moteid,oneFileData):
        self.moteAddress[moteid] = {}
        for d in oneFileData:
            if 'my16bID' in d:
                self.moteAddress[moteid]['my16bID'] = hex(d['my16bID'])

    def writeToFile(self,filename,data):
        with open(filename,'w') as f:
            pp = pprint.PrettyPrinter(indent=4)
            f.write(pp.pformat(data))
    
    # parse all files
    def parseAllFiles(self):
        for filename in os.listdir(LOGFILE_PATH):
            if filename.endswith('.log'):
                print 'Parsing {0}...'.format(filename),
                parsedFrames = self.parseOneFile(LOGFILE_PATH+filename)
                self.getFigure1Data(filename,parsedFrames)
                self.getFigure2Data(filename,parsedFrames)
                self.getFigure3Data(filename,parsedFrames)
                self.getFigure4Data(filename,parsedFrames)
                self.getMoteAddress(filename,parsedFrames)
                print 'done.'
        self.writeToFile('figure_1_schedule_vs_rank.txt',self.scheduletable)
        self.writeToFile('figure_2_syncTime_vs_numberMotes.txt',self.syncTime)
        self.writeToFile('figure_3_cellUsage_vs_numberCells.txt',self.cellUsage)
        self.writeToFile('figure_4_cellPDR.txt',self.cellPDR)
        self.writeToFile('moteAddress_map.txt',self.moteAddress)

    def parseOneFile(self,filename):
        self.hdlc  = OpenHdlc.OpenHdlc()
        (hdlcFrames,_) = self.hdlc.dehdlcify(filename)
        
        parsedFrames = []
        for f in hdlcFrames:
            # first byte is the type of frame
            if   f[0]==ord('D'):
                pf = self.parse_DATA(f[1:])
            elif f[0]==ord('S'):
                pf = self.parse_STATUS(f[1:])
            elif f[0]==ord('I'):
                pf = self.parse_INFO(f[1:])
            elif f[0]==ord('E'):
                pf = self.parse_ERROR(f[1:])
            elif f[0]==ord('C'):
                pf = self.parse_CRITICAL(f[1:])
            elif f[0]==ord('R'):
                pf = self.parse_REQUEST(f[1:])
            else:
                print 'TODO: parse frame of type {0}'.format(chr(f[0])) 
            if pf:
                parsedFrames += [pf]
        
        with open(filename+'.parsed','w') as f:
            f.write('\n'.join([str(pf) for pf in parsedFrames]))
        
        return parsedFrames
    
    #======================== level 1 parsers =================================
    
    def parse_DATA(self,frame):
        return {}
    def parse_STATUS(self,frame):
        header     = self.parseHeader(frame[:3],'<HB',('src','type'))
        payload    = {}
        if   header['type']==0: # IsSync
            payload = self.parseHeader(frame[3:],'<B',('isSync',))
        elif header['type']==1: # IdManager
            payload = self.parseHeader(
                frame[3:3+5],
                '>BHH',
                (
                    'isDAGroot',
                    'myPANID',
                    'my16bID',
                ),
            )
        elif header['type']==2: # MyDagRank
            payload = self.parseHeader(frame[3:],'<H',('myDAGrank',))
        elif header['type']==4: # Asn
            payload = self.parseHeader(
                frame[3:],
                '<BHH',
                (
                    'asn_4',                     # B
                    'asn_2_3',                   # H
                    'asn_0_1',                   # H
                ),
            )
        elif header['type']==6: # ScheduleRow
            payload = self.parseHeader(
                frame[3:],
                '<BHBBBBQQBBBBHHHB',
                (
                    'row',                       # B
                    'slotOffset',                # H 
                    'type',                      # B
                    'shared',                    # B
                    'channelOffset',             # B
                    'neighbor_type',             # B
                    'neighbor_bodyH',            # Q
                    'neighbor_bodyL',            # Q
                    'numRx',                     # B
                    'numTx',                     # B
                    'numTxACK',                  # B
                    'lastUsedAsn_4',             # B
                    'lastUsedAsn_2_3',           # H
                    'lastUsedAsn_0_1',           # H
                    'usageBitMap',               # H
                    'bitMapIndex',               # B
                ),
            )
        elif header['type']==9: # NeighborsRow
            payload = self.parseHeader(
                frame[3:],
                '<BBBBBBBBBBBBBBBBBBBBBBHbBBBBBHHB',
                (
                    'row',                       # B
                    'used',                      # B
                    'parentPreference',          # B
                    'stableNeighbor',            # B
                    'switchStabilityCounter',    # B
                    'addr_type',                 # B
                    'addr_128b_0',               # B
                    'addr_128b_1',               # B
                    'addr_128b_2',               # B
                    'addr_128b_3',               # B
                    'addr_128b_4',               # B
                    'addr_128b_5',               # B
                    'addr_128b_6',               # B
                    'addr_128b_7',               # B
                    'addr_128b_8',               # B
                    'addr_128b_9',               # B
                    'addr_128b_10',              # B
                    'addr_128b_11',              # B
                    'addr_128b_12',              # B
                    'addr_128b_13',              # B
                    'addr_128b_14',              # B
                    'addr_128b_15',              # B                     
                    'DAGrank',                   # H
                    'rssi',                      # b
                    'numRx',                     # B
                    'numTx',                     # B
                    'numTxACK',                  # B
                    'numWraps',                  # B
                    'asn_4',                     # B
                    'asn_2_3',                   # H
                    'asn_0_1',                   # H
                    'joinprio',                  # B
                ),
            )
        else:
            pass
        return payload
    def parse_INFO(self,frame):
        payload    = self.parseHeader(frame[:8],'<HBBHH',('moteID','component','errcode','arg1','arg2'))
        return payload
    def parse_ERROR(self,frame):
        payload    = self.parseHeader(frame[:8],'<HBBHH',('moteID','component','errcode','arg1','arg2'))
        return payload
    def parse_CRITICAL(self,frame):
        payload    = self.parseHeader(frame[:8],'<HBBHH',('moteID','component','errcode','arg1','arg2'))
        return payload
    def parse_REQUEST(self,frame):
        pass
    
    #======================== level 2 parsers =================================
    
    #======================== helpers =========================================
    
    def parseHeader(self,bytes,formatString,fieldNames):
        returnVal = {}
        fieldVals = struct.unpack(formatString, ''.join([chr(b) for b in bytes]))
        for (n,v) in zip(fieldNames,fieldVals):
            returnVal[n] = v
        return returnVal

#============================ main ============================================

def main():
    try:
        LogfileParser()
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
