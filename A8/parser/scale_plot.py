import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import string
import scipy as sp
import scipy.stats

import os
import traceback

import ast

FIGUREFILE_PATH           = './'
CELLTYPE_OFF              = 0
CELLTYPE_TX               = 1
CELLTYPE_RX               = 2
CELLTYPE_TXRX             = 3

MAXBUFFER_SCEHDULE        = 17 # 4 shared 3 serialRx 10 free buffer
SLOTFRAME_LENGTH          = 503

class plotFigure():
    def __init__(self):
        self.figureData = {}
        self.getFigureData()
        self.plotFigures()
        
    def getFigureData(self):
        for filename in os.listdir(FIGUREFILE_PATH):
            if filename.endswith('.txt'):
                print 'Getting data {0}...'.format(filename)
                with open(filename,'r') as f:
                    s = f.read()
                    self.figureData[filename] = ast.literal_eval(s)
                print 'Done.'
                
    def plotFigures(self):
        for filename in os.listdir(FIGUREFILE_PATH):
            if filename.endswith('.txt'):
                self.plotOneFigure(filename)
        # plt.show()
                
    def plotOneFigure(self,filename):
        if filename == 'cells_vs_rank.txt':
            self.plotCellsVSRankData()
        elif filename == 'networkSyncTime.txt':
            self.plotSynctimeVSNumberMotes()
        elif filename == 'cellUsage.txt':
            self.plotCellUsageVSNumberCells()
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
                if data[i]['type'] == CELLTYPE_TX :
                    numberOfCell += 1
            xData += [data['myDAGrank']['myDAGrank']]
            yData += [numberOfCell]
            totalCells += numberOfCell
        plt.plot(xData,yData,'*')
        plt.grid(True)
        plt.xlabel('DAGRank')
        plt.ylabel('Number Of Cells')
        plt.title('number cells VS DAGRank')
        plt.legend(['TotalCellsScheduled {0}'.format(totalCells)])
        plt.savefig('figures/cell_vs_rank.png')
        
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
        plt.plot(xData,yData,'-',label='TotalSyncedMotes {0}'.format(syncedMotes))
        plt.grid(True)
        plt.xlabel('Time (Second)')
        plt.ylabel('Number Of Motes')
        plt.title('sync time')
        plt.legend(loc=2)
        plt.savefig('figures/networkSyncTime.png')
        
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
            plt.savefig('figures/cellusage_vs_numbercells/cellusage_vs_numbercells_{0}.png'.format(moteid.split('.')[0][11:]))
        
    def plotCellPDR(self):
        fig4,ax1 = plt.subplots()
        ax2 = ax1.twinx()
        avgPdrData      = {}
        cellPresentTime = {}
        PdrData = [[[] for i in range(16)] for j in range(SLOTFRAME_LENGTH)]
        for moteid, data in self.figureData['cell_pdr.txt'].items():
            for cell, pdr in data.items():
                x = int(cell.split()[0])
                y = int(cell.split()[1])
                PdrData[x][y] += [float(pdr)]
                
                cell = '({0} {1})'.format(x,y)
                if cell in avgPdrData:
                    avgPdrData[cell] += [float(pdr)]
                else:
                    avgPdrData[cell] = [float(pdr)]
                    
                if cell in cellPresentTime:
                    cellPresentTime[cell] += 1
                else:
                    cellPresentTime[cell] = 1
                
        for cell, pdrlist in avgPdrData.items():
            avgPdrData[cell] = sum(pdrlist)/len(pdrlist)
        line1, = ax1.plot(range(len(avgPdrData)),avgPdrData.values(),'b-',label='cell pdr')
        line2, = ax2.plot(range(len(cellPresentTime)),cellPresentTime.values(),'r-',label='times cell being selected')
        ax1.set_xticks(range(len(cellPresentTime)))
        ax1.set_xticklabels(list(avgPdrData.keys()),rotation=90)
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
        plt.savefig('figures/cell_pdr.png') 
        
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
        plt.savefig('figures/reserveOverlap.png')
        
    def plotMotesIsNoRes(self):
        fig6 = plt.figure(6)
        isNoResData = {}
        for moteid, data in self.figureData['isNoResNeigbor.txt'].items():
            for row, nb_entry in data.items():
                if nb_entry['used']==1:
                    neighborId = hex(nb_entry['addr_128b_6']*255+nb_entry['addr_128b_7'])
                    if neighborId in isNoResData and nb_entry['isNoRes'] == 1:
                        isNoResData[neighborId] += 1
                    else:
                        if not (neighborId in isNoResData):
                            isNoResData[neighborId] = 0
        plt.plot(range(len(isNoResData)),isNoResData.values())
        plt.grid(True)
        plt.xticks(range(len(isNoResData)),list(isNoResData.keys()),rotation='vertical')
        plt.xlabel('Mote ID')
        plt.ylabel('Number times marked as \'isNoRes\'')
        plt.title('Number times marked as \'isNoRes\'')
        fig6.set_size_inches(18.5, 10.5)
        plt.savefig('figures/neighbor_isNoRes.png')
                        
                
        
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
    