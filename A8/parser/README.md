# Experiments Configuration and Modification 

This page records the configuration and related modification for each experiments deployed on IoT-Lab testbed (Saclay). 

## experiment 53720

### Modification

Added isNoRes field in neighbor table. Once the mote received sixtop response with RC_ERR_NORES return code, the neighbor will be marked as isNoRes and be deselecetd as parent. 

Related issue: https://openwsn.atlassian.net/browse/FW-575

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

## experiment 53730 

### Modification

Randomize the using shared slots. (light the traffic-contention on first several slots)

- Slot 1 has 30% possibility to be used if there is unicast packet to be sent.
- Slot 2 has 50% possibility to be used if there is unicast packet to be sent.
- Slot 3 will be used if there is unicast packet to be sent.


