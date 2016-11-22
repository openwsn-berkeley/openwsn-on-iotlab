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
543 cells have being selected during 90 minutes running.

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

## Experiment 53807

### Modification

Slotframe changed to 503.
Number of shared cells changed to 10.
Available free schedule entries increased to 20.
Sixtop TIMEOUT updated accordingly.

### Result

23 Tx cells are reserved after 60 minutes
315 cells have being selected during 60 minutes.
Take more time to get whole network to synchronize (over 100 seconds to get more than 90 nodes synchronized.)

### Possible reason

The long slotframe length makes the EB sending on the slot 0 more frequently, making the collision worse. 
The PDR of cells increased a little bit but still lots of cells have low PDR(<50%).

Probably mote select the neighbor with low rank but lower RSSI also at beginning.
Increase the stability of neighbor threshold. 

## Experiment 53811

### Modification

randomize EB sending period from {15 ~ 45} seconds. 
Increase the stability of neighbor threshold:

- BADNEIGHBORMAXRSSI        -60dBm
- GOODNEIGHBORMINRSSI       -70dBm

### Configuration

- 503 slotframe
- 10 shared slots:
	- Slot 1 and 2  have 20%   possibility to be used if there is unicast packet to be sent.
	- Slot 3 and 4  have 25%   possibility to be used if there is unicast packet to be sent.
	- Slot 5 and 6  have 33.3% possibility to be used if there is unicast packet to be sent.
	- slot 7 and 8  have 50%   possibility to be used if there is unicast packet to be sent.
	- slot 9 and 10 have 100%  possibility to be used if there is unicast packet to be sent.

## Result

All motes synchronized with 2 minutes. (With 101 slotframe and sending EB averagely 10 seconds, 90% motes synchronized within 1 minute).
The PDR of lots cells still stay low PDR (<50%).

## Experiment 53856

### Modification

Increase shared slots to 10.
Re-write the 
> Randomize the using shared slots. (light the traffic-contention on first several slots)

- Slot 1 and 2  have 66.6% possibility to be used if there is uni-cast packet to be sent.
- Slot 3 and 4  have 75%   possibility to be used if there is uni-cast packet to be sent.
- Slot 5 and 6  have 80%   possibility to be used if there is uni-cast packet to be sent.
- slot 7 and 8  have 83.3% possibility to be used if there is uni-cast packet to be sent.
- slot 9 and 10 have 100%  possibility to be used if there is uni-cast packet to be sent.

Chang back the stability of neighbor threshold:

- BADNEIGHBORMAXRSSI        -70dBm
- GOODNEIGHBORMINRSSI       -80dBm

Only choose the parent with RSSI greater than -90dbm.

## Result 

With 101 slotframe and sending EB averagely 10 seconds, 90% motes synchronized within 1 minute.
The PDR of lots cells still stay low PDR (<50%).
Lots of cells are chosen by several motes at same time. Increase the Slot Frame length may light this situation.


## Experiment 53865

### Modification
change to 307 slot frame

## Result

Less chance to be selected by two motes at same time. However, the PDR of lots cells still stay low PDR (<50%).
Only 8 Sixtop return messages are recorded through the whole network.

## Experiment 53868

### Modification

change to 101 slot frame
Only choose the parent with RSSI greater than -80 dbm.

Disable the 
> Randomize the using shared slots. (light the traffic-contention on first several slots)

## Result

The PDR of lots cells still stay low PDR (<50%).

Sixtop:

- Receive Sixtop response at senddone status. This is caused by the response side, it takes long time to send sixtop response back (because of backoff, retries and waiting time when multiple sixtop response to send in buffer).  
- Clear request happened 253 times with RC_SUCCESS, this means the parent changed frequently, and the cells to non-parent will be removed during the schedule housekeeping.  
- Add request happened 1176 times with RC_SUCCESS.
- Add request happened 27 times with RC_NORES.
- Delete request happened 133 times with RC_SUCCESS. 

## Experiment TBD

### Modification

- Don't remove the parent if there is no activity heard from it.
- Correct the TIMEOUT of sixtop
- Only allow one sixtop transaction at one time. (To support multiple transaction, it required to maintain multiple state machine for each sixtop transaction.)


### Actions/Ideas

- Don't remove Rx cell one side in schedule housekeeping. Maybe because the PDR on that cells is low, there may be collisions on that cell. Let SF handle this.
- Don't do sixtop relocation in housekeeping. Integrate it into SF function.
	- Do the relocation when no needs to add or delete cells.
	- Relocate cells with PDR<50%.
	- By default, all cells have usage of cell (ThresholdAdd+ThresholdDelete)/2

- The numTx and numTxAck in neighbor table should only used for Tx cells, not depending on all uni-cast packet. Since They are sent on shared slots also, which can't tell the really quality of the link. It's wrong to be used in this way when calculting the neighbor rank.
- In neighbor housekeeping, parent shouldn't be removed because of no activity heard recently. Parent doesn't send packet to children, the EB/DIO can't be used to update the activity of parent/mote, especially in a density network.


## Experiment 55586

### Previous review

With the iot-lab_M3 driver located in openwsn-berkeley/openwsn-fw repository, part of the iot-lab_(A8-)M3 nodes stops sending serial data even at the status of joining. Reserve mote than 90 nodes on Saclay site, more than 10 nodes will stop sending serial data during 20 minutes experiment deployment.

### Modification

Replace iot-lab_M3 nodes driver by openmotestm. 
https://github.com/openwsn-berkeley/openwsn-fw/commit/156f02a597176e799e396ebdf0300174d6dfc368


The implementation is for A8 nodes. The only different between M3 and A8 M3 is that they uses different spi port. M3 (SPI1) A8_M3 (SPI2)

### Result

- All nodes send serial data within 30 minutes experiment deployment.
- TBC.


 
 
