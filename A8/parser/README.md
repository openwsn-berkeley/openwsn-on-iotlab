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
- Only allow one sixtop transaction at one time. (To support multiple sixtop transaction, it required to maintain multiple state machine for each sixtop transaction.)


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

With the IoT-lab M3 driver located in openwsn-berkeley/openwsn-fw repository, part of the iot-lab_(A8-)M3 nodes stops sending serial data even at the status of joining. Reserve mote than 90 nodes on Saclay site, more than 10 nodes will stop sending serial data during 20 minutes experiment deployment.

### Modification

Replace iot-lab_M3 nodes driver by openmotestm. 
https://github.com/openwsn-berkeley/openwsn-fw/commit/156f02a597176e799e396ebdf0300174d6dfc368


The implementation is for A8 nodes. The only different between M3 and A8 M3 is that they uses different spi port. M3 (SPI1) A8_M3 (SPI2)

### Result

- All nodes send serial data within 30 minutes experiment deployment.


## Experiment 55617

### Modification

No Modification. Just start node-a8-2 as dagroot.

### Result

- Without 1 hour test, 10 nodes stops sending packet through serial port. This is less than the experiment done with old M3 driver.
- lots cells' PDR are very low. Through looking inside the gathered data, the Rx cells on the receiver side somehow disappeared (only one side). As a result, transmission failed without ACK. This is caused by housekeeping which remove Rx cell if no activity is detected with 2* DESYNCTIMEOUT
 
## Experiment 55862 

### Modification

- Remove the RxCell housekeeping functionality. (Don't do anything if we don't know the exactly reason why Rx Cell has no activity.)

### Result

- lots of cells' PDR are still low. 


---
## Experiment 55994

### Modification

- initialize the cell usage value as target value (60% usage)
- Don't send DIO if no parent is selected yet. (Since the mote is using a threshold to filter low rssi neighbor) if all neighbor has lower RSSI, the mote may doesn't have parent before receiving some packet from closer neighbor)
- Only generate DAO when the mote has a Tx cell for sending to parent.

### Result

- lots of cells' PDR are low
- DE-synchronization happens too much
	- the de-synchronization is set to 40 seconds and keepalive timeout is set to 30 seconds. The DAO is sent per 30 seconds. The time offset of child may already too much after 30 seconds, which exceeds the guard time.

## Experiment 56044 & 56055

### Modification 

- extend the desynchronization and have 20 seconds of Keepalive timeout
- EB/DIO is sent only mote has a Tx cell (not including DAGroot)


### Result

- too much desychronization happens (>4000 times for aroudn 100 nodes)
- lots Cell's PDR are low.

### Analysis

The time correction is observed large sometime, to make sure the general drift between two motes on IoT-Lab. we did exepriement 56088

### sub Experiment 56088 & 56140 & 56211 & 56217

- time correction is kind large since the packet is sent with long interval.

## Experiment 56331

### Modification

- increase Tx power to -7 dbm to insure the quality of link (use -17 dbm (lowest) before)

### Result

- cells' PDRs are improved certain level, but not that good.


## Experiment 56333

### Modification 

- increase Tx power to -3dbm, 
- RSSI threshold for stable neighbor is set to (-60)-(-70)
- if the neighbor rssi is lower than -60, don't record this neighbor


### result

- PDR is still low
- Some nodes have higher PDR at beginning (always 100%), once it lost packet, never recover, finally de-synced.
	- two reason for this result:
		- The node has higher timeCorrection before losing packet. Also the nodes is far from dagroot, (lots hop to dagroot.) This may caused the parent's synchronization changed its local time clock, the same happened to the parent node's parent. "Synchronization swing" in paper adaptive sync
		- for some nodes, which has low rank, needs to forward lots packet to it parent. When the cell is not enough, sfx will trigger 6top to add more. Before the 6top transcation finished, more packet arrived. The nodes has no more buffer to handle other transmission. (like ACK or if 6top failed, no more buffer for a new 6top transcation)


### Decision

- make Ka send frequently than the application packet to keep synch'ed
- Always reserve some buffer for 6top transaction.
 
## Experiment 56337 (25 nodes)

### Modification

- Make KA send after 5 second not heard anything. Desync to 15 seconds
- first 4 cells in the queue are reserved for packet creator with id lower than sixtop_res

### result

almost all cells' PDR are high (around 100%)

## Experiment 56338 (with 20 minutes)

### Modification

No modification but with 100 nodes.

## result

- able to see >60 nodes in the routing page
- Some cell's PDR is still low
- Node 3->node2,  slotoffset 18 Tx is reserved on node 3 side, but Rx never on node 2 side. (TB investigated)
- error message: 'the slot {0} to be added is already in schedule': 2,


## Analysis

- tip1: increase the Ka period to support more hop network
- tip2: modify the rssi threshold value to get a less hop network
- find the reason why Rx part is not reserved
- tip3: print out something related to the timeCorrection

## Experiment 56375 (with 60 minutes, >95 nodes)

### pre-setup

- chang the PANID: FACE
	- during the experiment, I found some nodes I have't reserved(not able because of the ssh connection) appear in the routing graphic (I know it because that one used to work). So there are some motes lost its ssh connection but not reset. They are running the old version of code whcih will influence the experiment. Use a new PANID to filter those motes.

## result

- most cells have good PDR


## Experiment 56508

### pre-setup

- chang the PANID : ABCD

### Modification

- don't process received packet if something goes wrong (for example, no free buffer for ACK to send back)
- update the implementation for reserving packet created by component lower than sixtop_res 
	- the previous implementation reserve the first 4 entries in queue buffer for high priority component. But if packet to be forwarded will change from a high priority packet (IEEE802154E) to low priority packet (FORWARDING)
	- new implementation reserve the 4 entries out of 10 queue buffer. once there are number of low priority packet in buffer (Threshold), low priority component is not allowed to reserve free buffer. When packet needs to chang from IEEE802154e to FORWARDING, the packet will be dropped.

## result

- More cells have higher PDRs (183(total 196) cells have PDR percent > 90%)
- Some Tx cells are reserved on one side but no Rx cell on another side, this may caused by the collision on ACK tranmission
- Some Rx cells are removed on one side but the Tx cell remained on another side. This may cause the time out of sixtop delete/clear. The delete/clear response is received but the mote has wrong status. Rx side will removed it but Tx side will not do that. Since we force Unicast packet sending on Tx cell if a mote has, this Tx cell will never be deleted.

## Experiement 56600

### Modificaiton

- When getting Unicast packet to send out, sixtop packet have higher priority to be chosen then others.

### Result

TBR