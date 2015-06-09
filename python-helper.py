#!/usr/bin/python

import sys
import subprocess
import argparse

def parse_options():
    parser = argparse.ArgumentParser()
    
    parser.add_argument('-s','--site',
                        default     = 'rennes',
                        help        = 'select site',
                        )
    
    parser.add_argument('-m','--moteNumber',
                        type        = int,
                        default     = 30,
                        help        = 'select number of motes',
                        )
    
    parser.add_argument('-c', '--closeMotes',
                        action      = 'store_true',
                        default     = False,
                        help        = 'nodes are selected as close as possible, otherwise',
                        )
    
    parser.add_argument('-n', '--name',
                        default     = 'minimaltest',
                        help        = 'experiment name',
                        )

    parser.add_argument('-d', '--duration',
                        default     = '30',
                        help        = 'experiment duration in minutes',
                        )

    parser.add_argument('-r', '--reservation',
                        type        = int,
                        help        = ('experiment schedule starting : seconds '
                                       'since 1970-01-01 00:00:00 UTC'),
                        )

    parser.add_argument('-p', '--print',
                        dest        = 'print_json',
                        action      = 'store_true',
                        help        = 'print experiment submission'
                        )
    
    args = parser.parse_args()
    
    return args

def main():
    
    args = parse_options()
    firmware_dagroot_path='~/openwsn/openwsn-fw/build/wsn430v14_mspgcc/projects/common/03oos_openwsn_dagroot_prog.ihex'
    firmware_path='~/openwsn/openwsn-fw/build/wsn430v14_mspgcc/projects/common/03oos_openwsn_prog.ihex'
    nodes_not_working = set()
    
    print '+--------------------------------------+'
    print '|      selecting available nodes       |'
    print '+--------------------------------------+'
    print
    nodes_info=subprocess.check_output(['experiment-cli','info','--site',args.site,'-li'])
    nodes_alive = eval(nodes_info)['items'][0]['rennes']['wsn430']['Alive']
    nodes_alive = reduce(lambda x,y:x+y, \
                         [range(int(group.split('-')[0]),int(group.split('-')[-1])+1) for group in nodes_alive.split('+')])
    nodes_alive = list(set(nodes_alive)-nodes_not_working
    nodes_selected=[]
    if args.closeMotes:
        nodes_selected = nodes_alive[:args.moteNumber]
    else:
        len_nodes_alive=len(nodes_alive)
        factor=float(len_nodes_alive-1)/float(args.moteNumber-1)
        factor_diff=0
        while nodes_alive:
            nodes_selected += [nodes_alive.pop(0)]
            factor_int = int(factor + factor_diff)
            factor_diff = factor + factor_diff - factor_int
            for i in xrange(factor_int-1):
                if nodes_alive:
                    nodes_alive.pop(0)
    
    dagroot_to_reserve_string = str(nodes_selected[0])
    
    nodes_to_reserve_string = '+'.join([str(node) for node in nodes_selected])#[1:]])
    nodes_openvisualizer    = ','.join(['wsn430-'+str(node) for node in nodes_selected])
    
    print '+--------------------------------------+'
    print '|          reserving nodes             |'
    print '+--------------------------------------+'
    print
    
    experiment_id = subprocess.check_output(['experiment-cli','submit',
                                             '-n',args.name,
                                             '-d',args.duration,
                                             '-r',args.reservation,
                                             '-p',args.print_json,
                                             #'-l','{0},wsn430,{1},{2}'.format(args.site,dagroot_to_reserve_string,firmware_dagroot_path),
                                             '-l','{0},wsn430,{1},{2}'.format(args.site,nodes_to_reserve_string,firmware_path),
                                             ])
    experiment_id = eval(experiment_id)['id']
    
    print '+--------------------------------------+'
    print '|     waiting to start experiment      |'
    print '+--------------------------------------+'
    print
    output = subprocess.check_output(['experiment-cli','wait','-i','{}'.format(experiment_id)])
    
    print '+--------------------------------------+'
    print '|       running Openvisualizer         |'
    print '+--------------------------------------+'
    print
    subprocess.call(['python','openVisualizerWeb.py','--port','1234','--iotlabmotes',nodes_openvisualizer])
    
    print '+--------------------------------------+'
    print '|          delete experiment           |'
    print '+--------------------------------------+'
    print
    subprocess.call(['experiment-cli','stop','-i','{}'.format(experiment_id)])
    
#============================ main ============================================

if __name__=="__main__":
    main()
