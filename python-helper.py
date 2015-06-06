#!/usr/bin/python

#import os
#import sys
import subprocess

# groups = [group for group in sys.argv[1].split('+')]
# nodes = []
# for group in groups:
    # nodes_temp = group.split('-')
    # if len(nodes_temp) == 1:
        # nodes+=['wsn430-'+nodes_temp[0]]
    # elif len(nodes_temp) == 2:
        # for node in range(int(nodes_temp[0]), int(nodes_temp[1])+1):
            # nodes+=['wsn430-'+str(node)]
# print len(nodes)
# with open('change.txt','w') as f:
    # f.write('python openVisualizerWeb.py --port 1234 --iotlabmotes '+','.join(nodes))
        
def main():
    print '+--------------------------------------+'
    print '|      checking available nodes        |'
    print '+--------------------------------------+'
    nodes_info=subprocess.check_output(['experiment-cli','info','--site','rennes','-li'])
    nodes_alive=eval(nodes_info)['items'][0]['rennes']['wsn430']['Alive']
    nodes_alive=reduce(lambda x,y:x+y,[range(int(nodes_consecutive.split('-')[0]),int(nodes_consecutive.split('-')[-1])+1) for nodes_consecutive in nodes_alive.split('+')])
    len_nodes_alive=len(nodes_alive)
    factor=len_nodes_alive/100.0
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
    subprocess.call(['cd','~/openwsn/openwsn-sw/software/openvisualizer/bin/openVisualizerApp/'])
    subprocess.call(['python','openVisualizerWeb.py','--port','1234','--iotlabmotes','+'.join([str(node) for node in nodes_selected])])
    print '+--------------------------------------+'
    print '|          delete experiment           |'
    print '+--------------------------------------+'
    subprocess.call(['experiment-cli','stop','-i','{}'.format(experiment_id)])
    
#============================ main ============================================

if __name__=="__main__":
    main()
