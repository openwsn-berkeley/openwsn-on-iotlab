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
    nodes_info=subprocess.check_output(['experiment-cli','info','--site','rennes','-li'])
    nodes_alive=nodes_info['items'][0]['rennes']['wsn430']['Alive']
    print nodes_alive
    
#============================ main ============================================

if __name__=="__main__":
    main()