#!/usr/bin/python
import os
import time
import traceback
import StackDefines
import multiprocessing
import threading
import matplotlib.pyplot as plt
import numpy as np

#============================ defines =========================================

printLock = threading.Lock()
LOGFILE_PATH = 'nodeoutput/'
# LOGFILE_PATH = 'node_test/'
CELLTYPE_TX         = 1
CELLTYPE_TXRX       = 3

ADDR_64B            = 2

PARENTPREFERENCE    = 1
DAGROOT             = 'node-a8-2'

#============================ functions =======================================
def analyzeOneFile_rank_parent_txcell_vs_time(logfile, cpuid, figure_identifier):
    
    try:
        dict_rank_parent_txcell_vs_asn = {'DAGrank':[], 'parent':{}, 'num_parents': [], 'slotOffset':{}, 'num_txcell': [], 'minutes':[],'lowestRank':[]}
        with open(logfile,'r') as file:
            for line in file:
                dict_line = eval(line)
                if 'myDAGrank' in dict_line:
                    dict_rank_parent_txcell_vs_asn['DAGrank'].append(dict_line['myDAGrank'])
                if ('addr_bodyH' in dict_line):
                    if (dict_line['parentPreference'] > 0):
                        dict_rank_parent_txcell_vs_asn['parent'].update({dict_line['row']:dict_line['addr_bodyH']})
                    else:
                        if dict_line['row'] in dict_rank_parent_txcell_vs_asn['parent']:
                            del dict_rank_parent_txcell_vs_asn['parent'][dict_line['row']]
                    dict_rank_parent_txcell_vs_asn['num_parents'].append(len(dict_rank_parent_txcell_vs_asn['parent']))
                    if (dict_line['parentPreference'] == PARENTPREFERENCE):
                        if dict_line['numTxACK'] == 0:
                            rankIncrease = (3*16-2) * 256
                        else:
                            rankIncrease = (3*dict_line['numTx']/dict_line['numTxACK']-2) * 256
                        dict_rank_parent_txcell_vs_asn['lowestRank'].append(dict_line['DAGrank']+rankIncrease)
                    else:
                        if len(dict_rank_parent_txcell_vs_asn['lowestRank'])>0:
                            # add the previous lowest rank for scale the list matching the scale of time
                            dict_rank_parent_txcell_vs_asn['lowestRank'].append(dict_rank_parent_txcell_vs_asn['lowestRank'][-1])
                        else:
                            dict_rank_parent_txcell_vs_asn['lowestRank'].append(65535)
                if ('slotOffset' in dict_line):
                    if (dict_line['type'] == CELLTYPE_TX):
                        dict_rank_parent_txcell_vs_asn['slotOffset'].update({dict_line['row']:dict_line['slotOffset']})
                    else:
                        if dict_line['row'] in dict_rank_parent_txcell_vs_asn['slotOffset']:
                            del dict_rank_parent_txcell_vs_asn['slotOffset'][dict_line['row']]
                    dict_rank_parent_txcell_vs_asn['num_txcell'].append(len(dict_rank_parent_txcell_vs_asn['slotOffset']))
                elif ('asn_0_1' in dict_line) and (('addr_type' in dict_line) is False ):
                    dict_rank_parent_txcell_vs_asn['minutes'].append((dict_line['asn_0_1'] + 65536 * dict_line['asn_2_3'])*0.015/60)
        
        with printLock:
            print "gathering data from file {0} Done!".format(logfile)
        
        fig, ax1 = plt.subplots()
        min_x_scale = min(len(dict_rank_parent_txcell_vs_asn['minutes']),len(dict_rank_parent_txcell_vs_asn['DAGrank']),len(dict_rank_parent_txcell_vs_asn['num_parents']),len(dict_rank_parent_txcell_vs_asn['lowestRank']))
        ax1.plot(dict_rank_parent_txcell_vs_asn['minutes'][:min_x_scale],dict_rank_parent_txcell_vs_asn['lowestRank'][:min_x_scale],'r-')
        ax1.set_xlabel('time (minutes)')
        ax1.set_ylabel('lowestRank')
        ax1.set_ylim(0,70000)
        
        ax2 = ax1.twinx()
        ax2.plot(dict_rank_parent_txcell_vs_asn['minutes'][:min_x_scale],dict_rank_parent_txcell_vs_asn['num_parents'][:min_x_scale],'b-')
        ax2.plot(dict_rank_parent_txcell_vs_asn['minutes'][:min_x_scale],dict_rank_parent_txcell_vs_asn['num_txcell'][:min_x_scale],'g-')
        ax2.set_ylabel('num_parents/num_txcell')
        ax2.set_ylim(-1,6)
        plt.savefig('figures/{0}_rank-parent-txcell-vs-time.png'.format(figure_identifier))
        
    except Exception as err:
        print traceback.print_exc()

def analyzeOneFile_syncTime_rank_dc_tc_cellInstallDelay(logfile, cpuid, figure_identifier):
    
    try:
        dict_data = {'sync_time':0, 'lowestRank':[], 'dc': 0, 'tc':[], 'cell_install_delay': []}
        synced         = False
        cell_installed = False
        with open(logfile,'r') as file:
            for line in file:
                dict_line = eval(line)
                if ('asn_0_1' in dict_line) and (('addr_type' in dict_line) is False ):
                    if synced is False:
                        dict_data['sync_time']          = (dict_line['asn_0_1'] + 65536 * dict_line['asn_2_3'])*0.015
                    if cell_installed is False:
                        dict_data['cell_install_delay'] = (dict_line['asn_0_1'] + 65536 * dict_line['asn_2_3'])*0.015
                if ('isSync' in dict_line) and dict_line['isSync'] == 1:
                    synced = True
                if ('addr_bodyH' in dict_line):
                    if (dict_line['parentPreference'] == PARENTPREFERENCE):
                        if dict_line['numTxACK'] == 0:
                            rankIncrease = (3*16-2) * 256
                        else:
                            rankIncrease = (3*dict_line['numTx']/dict_line['numTxACK']-2) * 256
                        dict_data['lowestRank'].append(dict_line['DAGrank']+rankIncrease)
                    else:
                        if len(dict_data['lowestRank'])>0:
                            # add the previous lowest rank for scale the list matching the scale of time
                            dict_data['lowestRank'].append(dict_data['lowestRank'][-1])
                if 'numTicsTotal' in dict_line:
                    dict_data['dc'] = float(dict_line['numTicsOn'])/float(dict_line['numTicsTotal'])
                if ('errcode' in dict_line) and dict_line['errcode']==28:
                    dict_data['tc'].append(np.int16(dict_line['arg1']))
                if ('slotOffset' in dict_line):
                    if dict_line['type'] == CELLTYPE_TXRX and dict_line['neighbor_type'] == ADDR_64B:
                        cell_installed = True
        
        with printLock:
            print "gathering data from file {0} Done!".format(logfile)
        
        return dict_data
        
    except Exception as err:
        print traceback.print_exc()
        
#============================ main ============================================
def analyzeFiles(params):
    cpuid = params
    all_data = {}
    try:
        for filename in os.listdir(LOGFILE_PATH):
            if filename.endswith('.parsed') and int(filename[8])%4==cpuid:
                figure_identifier = filename.split('.')[0]
                # analyzeOneFile_rank_parent_txcell_vs_time(LOGFILE_PATH+filename,cpuid,figure_identifier)
                all_data[filename.split('.')[0]] = {}
                all_data[filename.split('.')[0]] = analyzeOneFile_syncTime_rank_dc_tc_cellInstallDelay(LOGFILE_PATH+filename,cpuid,figure_identifier)
        return all_data
    except Exception as err:
        print traceback.print_exc()

def main():
    multiprocessing.freeze_support()
    num_cpus = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(num_cpus)
    data_result = pool.map_async(analyzeFiles,[i for i in range(num_cpus)])
    while not data_result.ready():
        time.sleep(1)
    result = data_result.get()
    
    # collection all data in dict_all_data
    dict_all_data = {}
    for task_data in result:
        dict_all_data.update(task_data)
    
    # generate rank vs node 
    dict_node_rank_median = []
    for node, content in dict_all_data.items():
        dict_node_rank_median.append((np.median(content['lowestRank']),node))
    dict_node_rank_median = sorted(dict_node_rank_median)
    
    # generate rank list
    rank_statistic      = []
    tc_statistic        = []
    sync_time           = []
    cell_install_delay  = []
    duty_cycle          = []
    num_nodes           = []
    nodes_label         = []
    for (median, node) in dict_node_rank_median:
        if node == DAGROOT:
            print "pass dagroot {0}".format(node)
            continue
        rank_statistic.append(dict_all_data[node]['lowestRank'])
        tc_statistic.append(dict_all_data[node]['tc'])
        nodes_label.append('{0} {1}'.format(node.split('-')[0],node.split('-')[-1]))
        sync_time.append(dict_all_data[node]['sync_time'])
        cell_install_delay.append(dict_all_data[node]['cell_install_delay'])
        duty_cycle.append(dict_all_data[node]['dc'])
        num_nodes.append(len(sync_time))
        
    # rank distribution 
    fig, ax = plt.subplots(figsize=(32,20))
    ax.boxplot(rank_statistic)
    ax.set_xticklabels(nodes_label, rotation=45)
    ax.set_xlabel('nodes')
    ax.set_ylabel('rank')
    plt.savefig('performance/statistic_rank.png')
    plt.clf()
    
    # time correction distribution
    fig, ax = plt.subplots(figsize=(32,20))
    ax.boxplot(tc_statistic)
    ax.set_xticklabels(nodes_label, rotation=45)
    ax.set_xlabel('nodes')
    ax.set_ylabel('time correction (ticks)')
    plt.savefig('performance/statistic_tc.png')
    plt.clf()
    
    # sync time
    fig, ax = plt.subplots()
    ax.plot(sorted(sync_time),num_nodes,'-^')
    ax.set_xlabel('time (seconds)')
    ax.set_ylabel('num_sync_nodes')
    plt.savefig('performance/sync_time.png')
    plt.clf()
    
    # cell install delay
    fig, ax = plt.subplots()
    ax.plot(sorted(cell_install_delay),num_nodes,'-^')
    ax.set_xlabel('time (seconds)')
    ax.set_ylabel('num_nodes_having_dedicated_cell')
    plt.savefig('performance/cell_install_delay.png')
    plt.clf()
    
    # duty cycle
    fig, ax = plt.subplots(figsize=(32,20))
    ax.plot(duty_cycle,'-')
    ax.set_xticks([i for i in range(len(nodes_label))])
    ax.set_xticklabels(nodes_label, rotation=45)
    ax.set_xlabel('nodes')
    ax.set_ylabel('duty_cycle')
    ax.set_ylim(0,0.1)
    plt.savefig('performance/duty_cycle.png')
    plt.clf()
    raw_input()
        
if __name__ == "__main__":
    main()