import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import string
import scipy as sp
import scipy.stats

from scipy.optimize import curve_fit

import os
import traceback

import ast

FIGUREFILE_PATH           = 'analyzeResult/'
CELLTYPE_OFF              = 0
CELLTYPE_TX               = 1
CELLTYPE_RX               = 2
CELLTYPE_TXRX             = 3

MAXBUFFER_SCEHDULE        = 23 # 10 shared 3 serialRx 10 free buffer
SLOTFRAME_LENGTH          = 101

tcData = {}
firstCellData = {}

# ==== help fucntion
def func(x, a, b, c):
    return a * np.exp(-b * x) + c

                
def keyfunc1(k):
    return tcData[k]['myDAGrank']
    
def keyfunc2(k):
    return firstCellData[k]['myDAGrank']

# ==== module 
class plotFigure():
    def __init__(self,logfilePath):
        self.figureData = {}
        
        self.moteId = {}
        
        self.logfilePath = logfilePath
        if not (os.path.exists(os.path.dirname(self.logfilePath+'figures/cellusage_vs_numbercells/'))):
            os.makedirs(os.path.dirname(self.logfilePath+'figures/cellusage_vs_numbercells/'))
        self.getFigureData()
        self.getMoteId()
        self.plotFigures()
        
    # ================= helper ==========================
    
    def getMoteId(self):
        for moteid, data in self.figureData['moteId.txt'].items():
            number = moteid.split('.')[0].split('-')[-1]
            id     = data['my16bID']
            self.moteId[int(id,16)] = number
        # print sorted(self.moteId)
            
    def getFigureData(self):
        for filename in os.listdir(self.logfilePath+FIGUREFILE_PATH):
            if filename.endswith('.txt'):
                print 'Getting data {0}...'.format(filename)
                with open(self.logfilePath+FIGUREFILE_PATH+filename,'r') as f:
                    s = f.read()
                    self.figureData[filename] = ast.literal_eval(s)
                print 'Done.'
                
    def plotFigures(self):
        for filename in os.listdir(self.logfilePath+FIGUREFILE_PATH):
            if filename.endswith('.txt'):
                self.plotOneFigure(filename)
        # plt.show()
                
    def plotOneFigure(self,filename):
        if filename == 'cells_vs_rank.txt':
            self.plotCellsVSRankData()
            self.plotLinksPDR()
        elif filename == 'timeCorrection.txt':
            self.plotTimeCorrectionVSRank()
        elif filename == 'networkSyncTime.txt':
            self.plotSynctimeVSNumberMotes()
        elif filename == 'firstCellTime.txt':
            self.plotFirstCellTimeVSRank()
        elif filename == 'cellUsage.txt':
            # self.plotCellUsageVSNumberCells()
            pass
        elif filename == 'cell_pdr.txt':
            self.plotCellPDR()
        elif filename == 'isNoResNeigbor.txt':
            self.plotMotesIsNoRes();
        
    def plotCellsVSRankData(self):
        plt.figure(1)
        xData = []
        yData = []
        totalCells = 0
        for moteid, data in self.figureData['cells_vs_rank.txt'].items():
            numberOfCell = 0
            for i in range(MAXBUFFER_SCEHDULE):
                if not(i in data):
                    continue
                if data[i]['type'] == CELLTYPE_TX :
                    numberOfCell += 1
            if data['myDAGrank']['myDAGrank'] == 65535: 
                continue
            xData += [data['myDAGrank']['myDAGrank']]
            yData += [numberOfCell]
            totalCells += numberOfCell
        # popt, pcov = curve_fit(func, xData, yData, p0=(1, 1e-6, 1))
        plt.plot(xData,yData,'o',label='Schedule cells')
        # x_fit = np.linspace(0,65535,100000)
        # print popt
        # plt.plot(x_fit, func(x_fit, *popt), 'r-', label="Fitted Curve")
        plt.grid(True)
        plt.xlabel('DAGRank')
        plt.ylabel('Number Of Cells')
        plt.title('number cells VS DAGRank {0}'.format('TotalCellsScheduled {0}'.format(totalCells)))
        plt.legend()
        plt.savefig('{0}figures/cell_vs_rank.png'.format(self.logfilePath))
        
    def plotLinksPDR(self):
        plt.figure(9)
        fig9,ax1 = plt.subplots()
        linkList = {}
        
        for moteid, data in self.figureData['cells_vs_rank.txt'].items():
            sender = moteid.split('.')[0].split('-')[-1]
            for i in range(MAXBUFFER_SCEHDULE):
                if data[i]['type'] == CELLTYPE_TX:
                    byte0 = (data[i]['neighbor_bodyH']>>48) & 255
                    byte1 = (data[i]['neighbor_bodyH']>>56)
                    receiver = self.moteId[byte0*256+byte1]
                    if not (sender+'->'+receiver in linkList):
                        linkList[sender+'->'+receiver] = {}
                        linkList[sender+'->'+receiver]['numTx']     = data[i]['numTx']
                        linkList[sender+'->'+receiver]['numTxACK']  = data[i]['numTxACK']
                    else:
                        linkList[sender+'->'+receiver]['numTx']    += data[i]['numTx']
                        linkList[sender+'->'+receiver]['numTxACK'] += data[i]['numTxACK']
            numTxzeroList = {}
            for key in linkList:
                if linkList[key]['numTx'] == 0:
                    numTxzeroList[key] = 0
                else:
                    linkList[key]['pdr'] = float(linkList[key]['numTxACK'])/float(linkList[key]['numTx'])
            for i in numTxzeroList:
                del linkList[i]
        order = sorted(linkList)
        xData = np.int_([i for i in range(len(order))])
        yData = np.float_([linkList[key]['pdr'] for key in order])
        ax1.bar(xData,yData,label='Link Quality (PDR on {0} links)'.format(len(order)))
        ax1.set_xticks([i for i in range(len(order))])
        ax1.set_xticklabels(order,rotation=90)
        fig9.set_size_inches(40.5, 10.5)
        ax1.set_ylim(0,1.2)
        plt.grid(True)
        plt.ylabel('PDR')
        plt.title('link PDR')
        plt.legend()
        plt.savefig('{0}figures/linkPDR.png'.format(self.logfilePath))
        
    def plotSynctimeVSNumberMotes(self):
        plt.figure(2)
        xData = []
        yData = []
        asn = []
        syncedMotes = 0
        for moteid, data in self.figureData['networkSyncTime.txt'].items():
            if 'asn_0_1' in data:
                asn += [data['asn_0_1']*0.015]
                syncedMotes+=1
            else:
                continue
        xData = sorted(asn)
        yData = [i+1 for i in range(len(asn))]
        plt.plot(xData,yData,'^-',label='TotalSyncedMotes {0}'.format(syncedMotes))
        plt.grid(True)
        plt.xlabel('Time (Second)')
        plt.ylabel('Number Of Motes')
        plt.title('sync time')
        plt.legend(loc=2)
        plt.savefig('{0}figures/networkSyncTime.png'.format(self.logfilePath))
        
    def plotCellUsageVSNumberCells(self):
        numFigures = 0
        for moteid, data in self.figureData['cellUsage.txt'].items():
            plt.figure(10+numFigures)
            numFigures += 1
            xData  = []
            y1Data = []
            y2Data = []
            y3Data = []
            for item in data:
                xData  += [item[0]]
                y1Data += [item[1]]
                y2Data += [item[2]]
                if item[2]> 0:
                    y3Data += [float(item[1])/float(item[2])]
                else:
                    y3Data += [0]
            plt.plot(xData,y1Data,label='cell usage per slotframe')
            plt.plot(xData,y2Data,label='number of cell per slotframe')
            plt.plot(xData,y3Data,label='average cell usage per slotframe')
            plt.grid(True)
            plt.xlabel('SlotFrame Number')
            plt.ylabel('Cell Usage (Number of transmission in 10 Slotframes)')
            plt.title('Cell usage per slotframe on {0}'.format(moteid.split('.')[0][11:]))
            plt.legend()
            plt.savefig('{0}figures/cellusage_vs_numbercells/cellusage_vs_numbercells_{1}.png'.format(self.logfilePath,moteid.split('.')[0][11:]))
        
    def plotCellPDR(self):
        fig4,ax1 = plt.subplots()
        ax2 = ax1.twinx()
        avgPdrData      = {}
        moteidList      = {}
        cellPresentTime = {}
        PdrData = [[[] for i in range(16)] for j in range(SLOTFRAME_LENGTH)]
        for moteid, data in self.figureData['cell_pdr.txt'].items():
            id = moteid.split('.')[0].split('-')[-1]
            for cell, pdr in data.items():
                x = int(cell.split()[0])
                y = int(cell.split()[1])
                PdrData[x][y] += [float(pdr)]
                
                cell = '{0} {1}'.format(x,y)
                if cell in avgPdrData:
                    avgPdrData[cell] += [float(pdr)]
                else:
                    avgPdrData[cell] = [float(pdr)]
                    
                if cell in moteidList:
                    moteidList[cell] += [id]
                else:
                    moteidList[cell]  = [id]
                    
                if cell in cellPresentTime:
                    cellPresentTime[cell] += 1
                else:
                    cellPresentTime[cell] = 1
        
        for cell, pdrlist in avgPdrData.items():
            avgPdrData[cell] = sum(pdrlist)/len(pdrlist)
            
        order = sorted(avgPdrData)
        line1, = ax1.plot([avgPdrData[key] for key in order],'b-',label='cell pdr')
        line2, = ax2.plot([cellPresentTime[key] for key in order],'r-',label='times cell being selected')
        ax1.set_xticks(range(len(order)))
        # ax1.set_xticklabels(['{0} {1}'.format(key,moteidList[key]) for key in order],rotation=90)
        ax1.set_xticklabels(order,rotation=90)
        plt.xlim(0,len(avgPdrData))
        plt.grid(True)
        ax1.set_xlabel('cells (slotoffset channeloffset)')
        ax1.set_ylabel('packet delivery ratio',color='b')
        ax2.set_ylabel('cell being selected times',color='r')
        ax1.set_ylim(-0.1,4)
        ax2.set_ylim(-0.1,4)
        plt.legend(handles=[line1,line2])
        fig4.set_size_inches(150, 16.5)
        plt.title('Cell Packet Delivery Ratio. (Totally {0} cells have being reserved)'.format(len(avgPdrData)))
        plt.savefig('{0}figures/cell_pdr.png'.format(self.logfilePath)) 
        
        fig5= plt.figure(5)
        numTimeReservedData = [[len(PdrData[j][i]) if len(PdrData[j][i])>1 else 0 for i in range(16)] for j in range(SLOTFRAME_LENGTH)]
        plt.pcolor(np.float_(np.transpose(numTimeReservedData)),cmap='Blues',label='number of times cell being reserved')
        plt.colorbar()
        plt.grid(True)
        plt.xlabel('SlotOffset')
        plt.ylabel('Channeloffset')
        plt.title('cells reserved overlapping')
        plt.xlim(7,SLOTFRAME_LENGTH)
        plt.ylim(0,16)
        fig5.set_size_inches(40.5, 10.5)
        plt.savefig('{0}figures/reserveOverlap.png'.format(self.logfilePath))
        
    def plotMotesIsNoRes(self):
        fig6 = plt.figure(6)
        isNoResData = {}
        for moteid, data in self.figureData['isNoResNeigbor.txt'].items():
            for row, nb_entry in data.items():
                if nb_entry['used']==1:
                    neighborId = nb_entry['addr_128b_6']*256+nb_entry['addr_128b_7']
                    if neighborId in isNoResData and nb_entry['isNoRes'] == 1:
                        isNoResData[neighborId] += 1
                    else:
                        if not (neighborId in isNoResData):
                            isNoResData[neighborId] = 0
        
        plt.plot(range(len(isNoResData)),isNoResData.values())
        plt.grid(True)
        plt.xticks(range(len(isNoResData)),[self.moteId[key] for key in isNoResData.keys()],rotation='vertical')
        plt.xlabel('Mote ID')
        plt.ylabel('Number times marked as \'isNoRes\'')
        plt.title('Number times marked as \'isNoRes\'')
        fig6.set_size_inches(18.5, 10.5)
        plt.savefig('{0}figures/neighbor_isNoRes.png'.format(self.logfilePath))
                        
    def plotTimeCorrectionVSRank(self):
        fig7 = plt.figure(7)
        ax = fig7.add_subplot(111)
        for moteid, data in self.figureData['timeCorrection.txt'].items():
            id = moteid.split('.')[0].split('-')[-1]
            if not 'timeCorrection' in data:
                continue
            tcData[id] = {}
            tcData[id]['myDAGrank']         = data['myDAGrank']['myDAGrank']
            tcData[id]['maxTC']             = data['timeCorrection']
        
        order = sorted(tcData,key=keyfunc1)
        bp = ax.boxplot([tcData[key]['maxTC'] for key in order])
        ax.set_xticklabels(['{0} {1}'.format(tcData[key]['myDAGrank'],key)for key in order],rotation=90)
        # plt.grid(True)
        plt.xlabel('node rank')
        plt.ylabel('time correction (ticks)')
        plt.title('time correction vs rank')
        fig7.set_size_inches(40.5, 10.5)
        plt.savefig('{0}figures/timeCorrection.png'.format(self.logfilePath))
        
    def plotFirstCellTimeVSRank(self):
        fig8 = plt.figure(8)
        ax = fig8.add_subplot(111)
        for moteid, data in self.figureData['firstCellTime.txt'].items():
            id = moteid.split('.')[0].split('-')[-1]
            if len(data)==0:
                continue
                
            firstCellData[id] = {}
            firstCellData[id]['myDAGrank']  = data['myDAGrank']['myDAGrank']
            firstCellData[id]['asn']        = 0.015*data['asn']
            
        order = sorted(firstCellData,key=keyfunc2)
        ax.plot([firstCellData[key]['myDAGrank'] for key in order],[firstCellData[key]['asn'] for key in order],'o-',label='shared slots=9')
        plt.grid(True)
        plt.xlabel('node rank')
        plt.ylabel('first cell installed time (seconds)')
        plt.title('rank VS first cell installed VS number sharded slots')
        plt.legend()
        plt.savefig('{0}figures/firstCellTime.png'.format(self.logfilePath))

        
#============= public ===================
def main():
    try:
        plotFigure()
        # raw_input("Script ended normally. Press Enter to close.")
    except Exception as err:
        print traceback.print_exc()
        raw_input("Script CRASHED. Press Enter to close.")
        
# ================= main fucntion ==========================
if __name__ == '__main__':
    main()
    