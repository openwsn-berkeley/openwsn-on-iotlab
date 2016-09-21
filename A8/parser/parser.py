#!/usr/bin/python
import struct
import os
import time
from collections import namedtuple
import OpenHdlc
import traceback
import StackDefines
import pprint

LOGFILE_PATH = '52229/'

class fieldParsingKey(object):
    def __init__(self,length,val,name,structure,fields):
        self.length      = length
        self.val        = val
        self.name       = name
        self.structure  = structure
        self.fields     = fields

class LogfileParser(object):
    
    HDLC_FLAG              = '\x7e'
    HDLC_FLAG_ESCAPED      = '\x5e'
    HDLC_ESCAPE            = '\x7d'
    HDLC_ESCAPE_ESCAPED    = '\x5d'
    
    def __init__(self):
        
        # parse
        alldata = self.parseAllFiles()
        
        # analyze
        allflatdata = []
        for (k,v) in alldata.items():
            allflatdata += v
        
        # question 1: are all preferred parents stable neighbors?
        output = []
        for d in allflatdata:
            if 'parentPreference' in d:
                if d['parentPreference']==2:
                    output += [ 'rssi={0} stableNeighbor={1}'.format(d['rssi'],d['stableNeighbor'])]
        with open('question_1.txt','w') as f:
            f.write('\n'.join(output))
        
        # question 2: how many errors?
        errorcount = {}
        for d in allflatdata:
            if 'errcode' in d:
                errstring = StackDefines.errorDescriptions[d['errcode']]
                if errstring not in errorcount:
                    errorcount[errstring] = 0
                errorcount[errstring] += 1
        with open('question_2.txt','w') as f:
            pp = pprint.PrettyPrinter(indent=4)
            f.write(pp.pformat(errorcount))
            
        # question 3: last neighbor table of each mote
        neighbortable = {}
        for (moteid,data) in alldata.items():
            neighbortable[moteid] = {}
            for d in data:
                if 'parentPreference' in d:
                    if d['used']==1:
                        neighbortable[moteid][d['row']] = d
        with open('question_3.txt','w') as f:
            pp = pprint.PrettyPrinter(indent=4)
            f.write(pp.pformat(neighbortable))
        
        # question 4: rssi histogram
        rssivals = {}
        for (moteid,data) in neighbortable.items():
            rssivals[moteid] = []
            for (_,v) in data.items():
                
                rssivals[moteid] += [(v['addr_128b_6'],v['addr_128b_7'],v['rssi'])]
        with open('question_4.txt','w') as f:
            output = []
            for (k,v) in rssivals.items():
                output += ['{0}: {1}'.format(k,sorted(v))]
            f.write('\n'.join(output))
        
        # question 5: network churn
        
        # question 6: node id address mapping
        idAddressMapping = {}
        for (moteid,data) in alldata.items():
            idAddressMapping[moteid] = {}
            for d in data:
                if 'my16bID' in d:
                    d['my16bID'] = hex(d['my16bID'])
                    idAddressMapping[moteid] = d
                    break
        with open('question_6.txt','w') as f:
            pp = pprint.PrettyPrinter(indent=4)
            f.write(pp.pformat(idAddressMapping))
            
        # question 7: how many nodes sych-ed ever
        nodelist = {}
        for (moteid,data) in alldata.items():
            nodelist[moteid] = []
            for d in data:
                if 'isSync' in d and d['isSync']==1:
                    nodelist[moteid] += d
                    break
        with open('question_7.txt','w') as f:
            pp = pprint.PrettyPrinter(indent=4)
            f.write(pp.pformat(nodelist))
            
        # question 8: the latest activity of nodes
        asnvals = {}
        for (moteid,data) in alldata.items():
            asnvals[moteid] = []
            for d in data:
                if 'asn_0_1' in d and not('stableNeighbor' in d):
                    asnvals[moteid] = [(d['asn_0_1'],d['asn_2_3'],d['asn_4'])]
        with open('question_8.txt','w') as f:
            pp = pprint.PrettyPrinter(indent=4)
            f.write(pp.pformat(asnvals))
            
        # question 9: myDAGrank
        rankvals = {}
        for (moteid,data) in alldata.items():
            rankvals[moteid] = []
            for d in data:
                if 'myDAGrank' in d:
                    rankvals[moteid] += [(d['myDAGrank'])]
        with open('question_9.txt','w') as f:
            pp = pprint.PrettyPrinter(indent=4)
            f.write(pp.pformat(rankvals))
        
    def parseAllFiles(self):
        alldata = {}
        for filename in os.listdir(LOGFILE_PATH):
            if filename.endswith('.log'):
                print 'Parsing {0}...'.format(filename),
                alldata[filename] = self.parseOneFile(LOGFILE_PATH+filename)
                print 'done.'
        return alldata
    
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
        pass
    def parse_ERROR(self,frame):
        payload    = self.parseHeader(frame[:8],'<HBBHH',('moteID','component','errcode','arg1','arg2'))
        return payload
    def parse_CRITICAL(self,frame):
        pass
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

if __name__ == "__main__":
    main()
