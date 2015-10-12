# openwsn-on-iotlab

Installation
------------

ssh to one iot-lab-deployment with `your-account`:

```
your-account@iot-lab-deployment:~$
```

and run the following commands

```
mkdir openwsn
cd openwsn
git clone https://github.com/NicolaAccettura/openwsn-on-iotlab.git
cd openwsn-on-iotlab
./prepare.py
```

Start a reservation
-------------------

Default commands will reserve 20 wsn430:cc2420 motes on the selected iot-lab-deployment

```
./openwsn-on-iotlab start
```

Run OpenWSN
-----------

Default commands will enable 10 motes among the 20 reserved

```
./openwsn-on-iotlab run
```

Terminate OpenWSN
-----------------

Press Ctrl-C or, in another shell, run:

```
./openwsn-on-iotlab terminate
```

Stop the reservation
--------------------

```
./openwsn-on-iotlab stop
```
