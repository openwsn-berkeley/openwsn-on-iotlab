# OpenWSN on IoT-Lab A8-M3 nodes

This repository contains all related tools, documentation how to build a 100 ([A8-M3 ](https://www.iot-lab.info/hardware/a8/)) nodes network on [IoT-Lab](https://www.iot-lab.info).

## Repository structure 

- **experiement**
	-  ***exp_submit.py***, for submitting a new experiment
	-  ***install.py***, for installing dependency software to run OpenVisualizer
	-  ***moteProbe.py***, for gathering serial data from A8-M3 nodes
	-  ***OpenHdlc.py***, for parsing HDLC format serial data from A8-M3 nodes
	-  ***cmd_multpleNode.py***, for running commands remotely on multiple A8-M3 nodes
	-  ***runov.py***, for running OpenVisualizer on a given A8-M3 node and port
- **parser**
    -  ***parser.py***, for parsing serial data to readable content
    -  ***StackDefines.py***, description of stack defines

## Schedule experiment with multiple A8-M3 nodes on IoT-Lab

### login to IoT-Lab

Use ssh/putty to login in to IoT-Lab. You can refer [here](https://www.iot-lab.info/tutorials/configure-your-ssh-access/) for details.

    C:\Users\Tengfei> ssh <username>@saclay.iot-lab.info

### Prepare tools

Copy all scripts in the repository to IoT-Lab. You can use SCP to copy all scripts to IoT-Lab.
	
	C:\Users\Tengfei> git clone https://github.com/openwsn-berkeley/openwsn-on-iotlab.git
	C:\Users\Tengfei> cd openwsn-on-iotlab/A8
	C:\Users\Tengfei> scp -r experiment/* <username>@saclay.iot-lab.info:~/A8/

Git clone Openvisualizer on IoT-Lab server: [https://github.com/openwsn-berkeley/openwsn-sw/tree/develop_FW-548](https://github.com/openwsn-berkeley/openwsn-sw/tree/develop_FW-548)

	chang@saclay:~$ cd ~/A8/
    chang@saclay:~$ git clone https://github.com/openwsn-berkeley/openwsn-sw.git
	chang@saclay:~$ git checkout develop_FW-548

### Submit an experiment with multiple nodes

	chang@saclay:~$ cd ~/A8/experiment
	chang@saclay:~/A8/experiment$ python exp_submit.py 60 10
	>>> experiment-cli submit -d 60 -l 10,archi=a8:at86rf231+site=saclay
	{
	    "id": 52104
	}



- The first parameter **60** indicates the duration of the experiment in minutes.
- The second parameter **10** indicates the number of nodes to reserve.

Later on, you need following commands to make sure the submitting has accomplished.

	chang@saclay:~/A8/experiment$ experiment-cli get -p

If you see experiment information like below, the experiment is accomplished. If not, try it again later until you see it.

	{
	    "associations": null,
	    "deploymentresults": {
	        "0": [
	            "a8-1.saclay.iot-lab.info",
	            "a8-2.saclay.iot-lab.info",
	            "a8-3.saclay.iot-lab.info",
	            "a8-5.saclay.iot-lab.info",
	            "a8-6.saclay.iot-lab.info",
	            "a8-7.saclay.iot-lab.info",
	            "a8-9.saclay.iot-lab.info",
	            "a8-14.saclay.iot-lab.info",
	            "a8-16.saclay.iot-lab.info"
	        ],
	        "1": [
	            "a8-8.saclay.iot-lab.info"
	        ]
	    },
	    "duration": 60,
	    "firmwareassociations": null,
	    "mobilities": null,
	    "name": null,
	    "nodes": [
	        "a8-1.saclay.iot-lab.info",
	        "a8-2.saclay.iot-lab.info",
	        "a8-3.saclay.iot-lab.info",
	        "a8-5.saclay.iot-lab.info",
	        "a8-6.saclay.iot-lab.info",
	        "a8-7.saclay.iot-lab.info",
	        "a8-8.saclay.iot-lab.info",
	        "a8-9.saclay.iot-lab.info",
	        "a8-14.saclay.iot-lab.info",
	        "a8-16.saclay.iot-lab.info"
	    ],
	    "profileassociations": null,
	    "profiles": null,
	    "reservation": null,
	    "state": "Running",
	    "type": "physical"
	}


*Note: you may notice that the reserved nodes is not from 1 to 10 since they are not available on IoT-Lab. Remember the start of the reserved nodes (a8-1) and the end (a8-16), which will be used later.*

### Program multiple nodes
	
It may take a little while that the reserved nodes are ready to be used. Use 

	ssh root@node-a8-1

to verify the nodes are ready. Once you can login the nodes, logout and issue following command.

	chang@saclay:~/A8/experiment$ python cmd_multpleNode.py -c flash -s 1 -e 17
	>>> ssh -o "StrictHostKeyChecking no" root@node-a8-1 'source /etc/profile; flash_a8_m3 A8/03oos_openwsn_prog.exe'
	...

The command flashes a range of nodes starting from 1 to 17 (1-16, 17 is not included) in sequence.

- The first parameter **1** indicates the start of the range.
- The second parameter **17** indicates the end of the range plus one (16+1).

### Check programming result

The result of flashing is recorded in flash.log file. It records the number of nodes it tries to flash, the number of success and fail and the list of success and fail nodes.
	
	==== Flashing statistic result ====
	Try to flash 15 nodes:
	Success: 9 Failed: 6
	---Success List---
	1 2 3 5 6 7 9 14 16
	---failed List---
	4 10 11 12 13 15

### Install dependency software

	chang@saclay:~/A8/experiment$ python install.py

The software has to be installed on a8-m3-node as it requires *sudo* permission and there is not password on loged iot-lab server. Be default the command will log into a8-node-9 to install the software. Since the software is shared with all nodes, it not required to install again on each a8 nodes.

Note: It's recommended to zip the directory: /usr/lib/python2.7/site-packages/ into a tar.gz file under A8 folder. Since some packages may need compiling for installation and it takes too long time to finish. Unzip the tar.gz file to overwriten the /usr/lib/python2.7/site-packages will do that exactly same thing as 'python install.py' but with much less time.

To zip the site-packages folder: 

	chang@saclay:~/A8$ tar -czvf site-packages.tar.gz /usr/lib/python2.7/site-packages/
	
To unzip the tar.gz file:
	
	chang@saclay:~/A8$ ssh root@node-a8-2
	root@node-a8-2:~# cd A8/
	root@node-a8-2:~/A8# tar -xzf site-packages.tar.gz -C /

### Run moteProbe.py on multiple nodes

	chang@saclay:~/A8/experiment$ python cmd_multpleNode.py -c moteprobe -s 1 -e 17
	>>> ssh -f -o "StrictHostKeyChecking no" root@node-a8-1 'source /etc/profile; cd ~/A8/serialData/; python moteProbe.py &'
	>>> ssh -f -o "StrictHostKeyChecking no" root@node-a8-2 'source /etc/profile; cd ~/A8/serialData/; python moteProbe.py &'
	>>> ssh -f -o "StrictHostKeyChecking no" root@node-a8-3 'source /etc/profile; cd ~/A8/serialData/; python moteProbe.py &'
	>>> ssh -f -o "StrictHostKeyChecking no" root@node-a8-4 'source /etc/profile; cd ~/A8/serialData/; python moteProbe.py &'
	ssh: connect to host node-a8-4 port 22: Connection refused
	>>> ssh -f -o "StrictHostKeyChecking no" root@node-a8-5 'source /etc/profile; cd ~/A8/serialData/; python moteProbe.py &'
	...

The command run moteProbe.py on a range of nodes starting from 1 to 17 (1-16, 17 is not included) in sequence. The parameter is the same with flashing multiple nodes.

You will see the node-a8-x.log file in the same directory, which records the serialData sent by the node.

### Kill the python process running on a8 nodes

	chang@saclay:~/A8/experiment$ python cmd_multpleNode.py -c killpython -s 1
	>>> ssh -o "StrictHostKeyChecking no" root@node-a8-1 'source /etc/profile; killall python'
	...

The command kill the python process on node-a8-1 only. When the only -s is provide, only the mote indicated by -s will execute the command indicated by -c.

### Run Openvisualizer on a given a8 node and port

To see the openvisualizer web interface on your local machine, you need creating a forwarding tunnel when logging the iot-lab server. For example, forwarding a TCP tunnel with port 1234.

	C:\Users\Tengfei>ssh -L 1234:localhost:1234 chang@saclay.iot-lab.info

Then on iot-lab server, type in the following command:

	 chang@saclay:ssh -L 1234:localhost:1234 root@node-a8-1
	 root@node-a8-1:cd ~/A8/openwsn-sw/software/openvisualizer/
	 root@node-a8-1:sudo scons runweb --port 1234

Now you can open the Openvisualizer web interface through the browser on your local machine with following address.

	http://localhost:1234/

### Run Openvisualizer with Rover mode

	chang@saclay:~/A8/experiment$ python cmd_multpleNode.py -c runrover -s 1
	>>> ssh -n -f -o "StrictHostKeyChecking no" root@node-a8-105 'source /etc/profile; cd ~/A8/openwsn-sw/software/openvisualizer/bin/openVisualizerApp/; python openRoverApp.py &'

Then you need go over all steps at [running a network](https://openwsn.atlassian.net/wiki/display/OW/Running+a+Network) before **Start an Experiment** section. After you done that type the following command: 
    
    (venv)chang@saclay:~$cd A8/openwsn-sw/software/openvisualizer
    (venv)chang@saclay:~/A8/openwsn-sw/software/openvisualizer$scons runweb --rover --port=1234

Make sure you are in the virtual environment, indicated by the *(venv)* prefix on the commandline. Also make sure the iot-lab saclay site is ssh'ed with forwarding on 1234 port.

Now open http://localhost:1234 on your local computer in your browser and navigate to **Rovers** page. 

Then go over the steps at [Remote+control+your+mote+through+raspberry+pi](https://openwsn.atlassian.net/wiki/display/OW/Remote+control+your+mote+through+raspberry+pi) starting from **Play** section step 4. Choose the 
*eth0: 2001:660:3207:4bf::17* 
from the drop down list.

Create a file containing all nodes you downloaded with firmware and separate them with comma(,).

Here is an example of A8-M3 node address:  2001:660:3207:400::X
*2001:660:3207:400* is the ipv6 prefix with is shared by all A8 nodes.
X is the node id in hex format. 
E.g. the ipv6 address of A8 node-100 is 
2001:660:3207:400::64.

Following is the example of the node list file to upload (node 100, node 101, node 102,node 103, node 104): 

> 2001:660:3207:400::64,2001:660:3207:400::65,2001:660:3207:400::66,2001:660:3207:400::67,2001:660:3207:400::68


If everything goes well you will able to see the serial status information coming into Openvisualizer on **Motes** page.
