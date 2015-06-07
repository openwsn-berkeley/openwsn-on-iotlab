#!/usr/bin/python

import os
#import sys
import subprocess

def main():
    print '+--------------------------------------+'
    print '|      checking available nodes        |'
    print '+--------------------------------------+'
    nodes_info=subprocess.check_output(['experiment-cli','info','--site','rennes','-li'])
    nodes_alive=eval(nodes_info)['items'][0]['rennes']['wsn430']['Alive']
    nodes_alive=reduce(lambda x,y:x+y,[range(int(nodes_consecutive.split('-')[0]),int(nodes_consecutive.split('-')[-1])+1) for nodes_consecutive in nodes_alive.split('+')])
    len_nodes_alive=len(nodes_alive)
    factor=len_nodes_alive/30.0
    nodes_selected=[]
    factor_diff=0
    while nodes_alive:
        nodes_selected+=[nodes_alive.pop(0)]
        factor_int = int(factor + factor_diff)
        factor_diff = factor + factor_diff - factor_int
        for i in xrange(factor_int-1):
            if nodes_alive:
                nodes_alive.pop(0)
    nodes_to_reserve_string='+'.join([str(node) for node in nodes_selected])
    firmware_path='~/openwsn/openwsn-fw/build/wsn430v14_mspgcc/projects/common/03oos_openwsn_prog.ihex'
    print '+--------------------------------------+'
    print '|          reserving nodes             |'
    print '+--------------------------------------+'
    experiment_id=subprocess.check_output(['experiment-cli','submit','-n','minimaltest','-d','30','-l','rennes,wsn430,{0},{1}'.format(nodes_to_reserve_string,firmware_path)])
    experiment_id=eval(experiment_id)['id']
    print '+--------------------------------------+'
    print '|     waiting to start experiment      |'
    print '+--------------------------------------+'
    subprocess.call(['experiment-cli','wait','-i','{}'.format(experiment_id)])
    print '+--------------------------------------+'
    print '|       running Openvisualizer         |'
    print '+--------------------------------------+'
    subprocess.call(['python','~/openwsn/openwsn-sw/software/openvisualizer/bin/openVisualizerApp/openVisualizerWeb.py','--port','1234','--iotlabmotes','+'.join([str(node) for node in nodes_selected])])
    print '+--------------------------------------+'
    print '|          delete experiment           |'
    print '+--------------------------------------+'
    subprocess.call(['experiment-cli','stop','-i','{}'.format(experiment_id)])
    
#============================ main ============================================

if __name__=="__main__":
    main()
