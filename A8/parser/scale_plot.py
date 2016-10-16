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
                if data[i]['type'] == CELLTYPE_TX or data[i]['type'] == CELLTYPE_RX:
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
        plt.plot(xData,yData,'*')
        plt.grid(True)
        plt.xlabel('Time (Second)')
        plt.ylabel('Number Of Motes')
        plt.title('sync time')
        plt.legend(['TotalSyncedMotes {0}'.format(syncedMotes)])
        plt.savefig('figures/networkSyncTime.png')
        
    def plotCellUsageVSNumberCells(self):
        plt.figure(3)
        xData = []
        yData = []
        for moteid, data in self.figureData['cellUsage.txt'].items():
            for item in data:
                xData += [item[0]]
                yData += [item[1]]
            plt.plot(xData,yData,label=moteid)
        plt.grid(True)
        plt.xlabel('SlotFrame Number')
        plt.ylabel('Cell Usage (Number of transmission in last 10 Slotframes)')
        plt.title('Cell usage per slotframe')
        plt.legend()
        plt.savefig('figures/cellusage_vs_numbercells.png')
        
    def plotCellPDR(self):
        plt.figure(4)
        xData = [i for i in range(101)]
        yData = {}
        for moteid, data in self.figureData['cell_pdr.txt'].items():
            plt.plot(xData,data)
        plt.grid(True)
        plt.xlabel('SlotOffset')
        plt.ylabel('Cell Packet Delivery Ratio')
        plt.title('Cell Packet Delivery Ratio')
        plt.savefig('figures/cell_pdr.png')
        
    def plotMotesIsNoRes(self):
        fig5 = plt.figure(5)
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
        fig5.set_size_inches(30, 16)
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
    