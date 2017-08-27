#!/usr/bin/python
import struct
import os
import sys
sys.path.append(os.path.abspath('../experiment'))
import OpenHdlc
import traceback
import StackDefines

#============================ defines =========================================

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
    
    def __init__(self,logfilePath):

        self.scheduletable  = {}
        self.syncTime       = {}
        self.cellUsage      = {}
        self.cellPDR        = {}
        self.moteAddress    = {}
        self.logfilePath    = logfilePath
        # parse
        self.parseAllFiles()
    
    def parseAllFiles(self):
        for filename in os.listdir(self.logfilePath):
            if filename.endswith('.log'):
                print 'Parsing {0}...'.format(filename),
                with open('parser.log','a') as f:
                    f.write("{0}\n".format(filename))
                self.parseOneFile(self.logfilePath+filename)
                print 'done.'

    def parseOneFile(self,filename):
        self.hdlc  = OpenHdlc.OpenHdlc()
        (hdlcFrames,_) = self.hdlc.dehdlcify(filename)
        
        parsedFrames = []
        for f in hdlcFrames:
            if not f:
                continue
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
        elif header['type']==3: # OutputBuffer
            payload = self.parseHeader   (
                frame[3:],
                '<HH',
                (
                    'index_write',               # H
                    'index_read',                # H
                ),
            )
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
        elif header['type']==5: # Macstates
            payload = self.parseHeader(
                frame[3:],
                '<BBhhBII',
                (
                    'numSyncPkt' ,               # B
                    'numSyncAck',                # B
                    'minCorrection',             # h
                    'maxCorrection',             # h
                    'numDeSync',                 # B
                    'numTicsOn',                 # I
                    'numTicsTotal',              # I
                ),
            )
        elif header['type']==6: # ScheduleRow
            payload = self.parseHeader(
                frame[3:],
                '<BHBBBBQQBBBBHH',
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
                ),
            )
        elif header['type']==7: # Backoff
            payload = self.parseHeader   (
                frame[3:],
                '<BB',
                (
                    'backoffExponent',           # B
                    'backoff',                   # B
                ),
            )
        elif header['type']==8: # QueueRow
            payload = self.parseHeader(
                frame[3:],
                '<BBBBBBBBBBBBBBBBBBBBBBBBBBBBBB',
                (
                    'creator_0',                 # B
                    'owner_0',                   # B
                    'creator_1',                 # B
                    'owner_1',                   # B
                    'creator_2',                 # B
                    'owner_2',                   # B
                    'creator_3',                 # B
                    'owner_3',                   # B
                    'creator_4',                 # B
                    'owner_4',                   # B
                    'creator_5',                 # B
                    'owner_5',                   # B
                    'creator_6',                 # B
                    'owner_6',                   # B
                    'creator_7',                 # B
                    'owner_7',                   # B
                    'creator_8',                 # B
                    'owner_8',                   # B
                    'creator_9',                 # B
                    'owner_9',                   # B
                    'creator_10',                # B
                    'owner_10',                  # B
                    'creator_11',                # B
                    'owner_11',                  # B
                    'creator_12',                # B
                    'owner_12',                  # B
                    'creator_13',                # B
                    'owner_13',                  # B
                    'creator_14',                # B
                    'owner_14',                  # B
                ),
            )
        elif header['type']==9: # NeighborsRow
            payload = self.parseHeader(
                frame[3:],
                '<BBBBBBBQQHbBBBBBHHBBBB',
                (
                    'row',                       # B
                    'used',                      # B
                    'insecure',                  # B
                    'parentPreference',          # B
                    'stableNeighbor',            # B
                    'switchStabilityCounter',    # B
                    'addr_type',                 # B
                    'addr_bodyH',                # Q
                    'addr_bodyL',                # Q
                    'DAGrank',                   # H
                    'rssi',                      # b
                    'numRx',                     # B
                    'numTx',                     # B
                    'numTxACK',                  # B
                    'numWraps',                  # B
                    'asn_4',                     # B
                    'asn_2_3',                   # H
                    'asn_0_1',                   # H
                    'joinPrio',                  # B
                    'f6PNORES',                  # B
                    'sixtopGEN',                 # B
                    'sixtopSeqNum',              # B
                ),
            )
        else:
            pass
        return payload
    def parse_INFO(self,frame):
        payload    = self.parseHeader(frame[:8],'>HBBHH',('moteID','component','errcode','arg1','arg2'))
        return payload
    def parse_ERROR(self,frame):
        payload    = self.parseHeader(frame[:8],'>HBBHH',('moteID','component','errcode','arg1','arg2'))
        return payload
    def parse_CRITICAL(self,frame):
        payload    = self.parseHeader(frame[:8],'>HBBHH',('moteID','component','errcode','arg1','arg2'))
        return payload
    def parse_REQUEST(self,frame):
        pass
    
    #======================== helpers =========================================
    
    def parseHeader(self,bytes,formatString,fieldNames):
        returnVal = {}
        try:
            fieldVals = struct.unpack(formatString, ''.join([chr(b) for b in bytes]))
            for (n,v) in zip(fieldNames,fieldVals):
                returnVal[n] = v
        except:
            with open('parser.log','a') as f:
                f.write(str([b for b in bytes]))
            returnVal = {}
        return returnVal

#============================ main ============================================

def main():
    try:
        LogfileParser(LOGFILE_PATH)
        raw_input("Script ended normally. Press Enter to close.")
    except Exception as err:
        print traceback.print_exc()
        raw_input("Script CRASHED. Press Enter to close.")

#============================ helper ==========================================

        
if __name__ == "__main__":
    main()
