#!/usr/bin/python
import struct
import os
import sys
sys.path.append(os.path.abspath('../experiment'))
import OpenHdlc
import traceback
import StackDefines
import threading
import multiprocessing
import time

#============================ define ==========================================

HDLC_FLAG              = '\x7e'
HDLC_FLAG_ESCAPED      = '\x5e'
HDLC_ESCAPE            = '\x7d'
HDLC_ESCAPE_ESCAPED    = '\x5d'

#============================ class ===========================================

def oneFileParser(logfilePath):

        hdlc  = OpenHdlc.OpenHdlc()
        (hdlcFrames,_) = hdlc.dehdlcify(logfilePath)
        
        parsedFrames = []
        for f in hdlcFrames:
            if not f:
                continue
            # first byte is the type of frame
            if   f[0]==ord('D'):
                pf = parse_DATA(f[1:])
            elif f[0]==ord('S'):
                pf = parse_STATUS(f[1:])
            elif f[0]==ord('I'):
                pf = parse_INFO(f[1:])
            elif f[0]==ord('E'):
                pf = parse_ERROR(f[1:])
            elif f[0]==ord('C'):
                pf = parse_CRITICAL(f[1:])
            elif f[0]==ord('R'):
                pf = parse_REQUEST(f[1:])
            else:
                print 'TODO: parse frame of type {0}'.format(chr(f[0])) 
            if pf:
                parsedFrames += [pf]
        
        with open(logfilePath+'.parsed','w') as f:
            f.write('\n'.join([str(pf) for pf in parsedFrames]))
        
        print 'Parsing {0}...Done!'.format(logfilePath)
        

def parseFiles(params):
    LOGFILE_PATH = 'nodeoutput/'
    cpuid,num_cpus = params
    try:
        for filename in os.listdir(LOGFILE_PATH):
            if filename.endswith('.log') and int(filename[8])%num_cpus==cpuid:
                with open('parser.log','a') as f:
                    f.write("{0}\n".format(filename))
                figure_identifier = filename.split('.')[0]
                oneFileParser(LOGFILE_PATH+filename)
    except Exception as err:
        print traceback.print_exc()
            
def main():
    multiprocessing.freeze_support()
    num_cpus = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(num_cpus)
    data_result = pool.map_async(parseFiles,[(i,num_cpus) for i in range(num_cpus)])
    while not data_result.ready():
        time.sleep(1)
    result = data_result.get()
        
if __name__ == "__main__":
    main()
    
#============================ parser function =================================

def parse_DATA(frame):
    header     = parseHeader(frame[:7],'<HHHB',('src','asn_0_1','asn_2_3','asn_4'))
    payload    = {'data': str([byte for byte in frame[7:]])}
    return payload
    
def parse_STATUS(frame):
    header     = parseHeader(frame[:3],'<HB',('src','type'))
    payload    = {}
    if   header['type']==0: # IsSync
        payload = parseHeader(frame[3:],'<B',('isSync',))
    elif header['type']==1: # IdManager
        payload = parseHeader(
            frame[3:3+5],
            '>BHH',
            (
                'isDAGroot',
                'myPANID',
                'my16bID',
            ),
        )
    elif header['type']==2: # MyDagRank
        payload = parseHeader(frame[3:],'<H',('myDAGrank',))
    elif header['type']==3: # OutputBuffer
        payload = parseHeader   (
            frame[3:],
            '<HH',
            (
                'index_write',               # H
                'index_read',                # H
            ),
        )
    elif header['type']==4: # Asn
        payload = parseHeader(
            frame[3:],
            '<BHH',
            (
                'asn_4',                     # B
                'asn_2_3',                   # H
                'asn_0_1',                   # H
            ),
        )
    elif header['type']==5: # Macstates
        payload = parseHeader(
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
        payload = parseHeader(
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
        payload = parseHeader   (
            frame[3:],
            '<BB',
            (
                'backoffExponent',           # B
                'backoff',                   # B
            ),
        )
    elif header['type']==8: # QueueRow
        payload = parseHeader(
            frame[3:],
            '<BBBBBBBBBBBBBBBBBBBB',
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
            ),
        )
    elif header['type']==9: # NeighborsRow
        payload = parseHeader(
            frame[3:],
            '<BBBBBBBQQHbBBBBBHHBBBBBB',
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
                'inBlacklist',               # B
                'sixtopSeqNum',              # B
                'backoffExponent',           # B
                'backoff',                   # B
            ),
        )
    else:
        pass
    return payload
    
def parse_INFO(frame):
    payload    = parseHeader(frame[:8],'>HBBHH',('moteID','component','errcode','arg1','arg2'))
    return payload

def parse_ERROR(frame):
    payload    = parseHeader(frame[:8],'>HBBHH',('moteID','component','errcode','arg1','arg2'))
    return payload
    
def parse_CRITICAL(frame):
    payload    = parseHeader(frame[:8],'>HBBHH',('moteID','component','errcode','arg1','arg2'))
    return payload
    
def parse_REQUEST(frame):
    pass

def parseHeader(bytes,formatString,fieldNames):
    returnVal = {}
    try:
        fieldVals = struct.unpack(formatString, ''.join([chr(b) for b in bytes]))
        for (n,v) in zip(fieldNames,fieldVals):
            returnVal[n] = v
    except:
        with open('parser.log','a') as f:
            f.write(str([b for b in bytes]))
        print formatString
        returnVal = {}
    return returnVal
