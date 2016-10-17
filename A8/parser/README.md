# Experiments Configuration and Modification 

This page records the configuration and related modification for each experiments deployed on IoT-Lab testbed (Saclay). 

## Experiment 53720

### Modification

Added isNoRes field in neighbor table. Once the mote received sixtop response with RC_ERR_NORES return code, the neighbor will be marked as isNoRes and be deselecetd as parent. 

Related issue: https://openwsn.atlassian.net/browse/FW-575

A piggyback EB_DIO packet is implemented.

Related commit: https://github.com/openwsn-berkeley/openwsn-fw/commit/803b57325271f584cb584ab5b83617b44dadd2a5


### Configuration

- 101 slotframe
- 4 shared slots:
	- 0: for sending piggyback EB_DIO
	- 1~3: for sending unicast Packet if there is no dedicated cell reserved.
- isNoRes field never clear
- housekeeping (neighbor):
	- remove no activity neighbor (in 30 seconds), not include isNoRes marked neighbor
	- only keep **3 lowest rank** neighbor in table
- housekeeping (schedule):
	- remove no activity neighbor (in 2* DE-SYNC time)
	- clear Tx Cell to non-parent neighbor
	- remove Tx Cell which PDR is lower than 50%, reserve one before removing that cell.


### Result 

Only less than 20 Tx cells are reserved after 60 minutes.

### Possible reason

The collision on shared slots are too much. Since the first shared slots for sending unicast cell has much higher chance to be chosen, as a result it has a higher collision ratio than others. Randomize the using of shared slots for sending unicast packet.

## Experiment 53730 

### Modification

Randomize the using shared slots. (light the traffic-contention on first several slots)

- Slot 1 has 30% possibility to be used if there is unicast packet to be sent.
- Slot 2 has 50% possibility to be used if there is unicast packet to be sent.
- Slot 3 will be used if there is unicast packet to be sent.


### Result

Only 17 Tx Cells are reserved after 90 minutes.
543 cells are selected during 90 minutes running.

### Possible reason
The reserved cells through the network has a higher ratio of overlapping (same cell are selected by lots of motes).

## Experiment 53790

### Modification

Nothing modified. Just run a 20 minutes network, to see how many mote can synchronize with fisrt EB. The dagroot choose a mote (node-a8-60) which is in the center of the phyical position deployment on Saclay site.

Check the topology: https://www.iot-lab.info/testbed/maps.php?site=saclay

### Result

41 motes synchronized at the first EB sent by dagroot. This provded that there is much higher chance to have two same cells used for sending at same time. 

### Possible solution

Increase the slotframe length to 503. 

