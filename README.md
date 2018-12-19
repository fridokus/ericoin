# ericoin
Test implementation of a p2p PoW cryptocurrency in python

## How to run
Start by running ``generate_keys.py``. This will create a private and public key.

``setup_2_miners_1_bookkeeper.py`` can be run in Windows as a quickstart, otherwise you'll have to figure out some stuff.. look at that script to figure out what to do.

## Register remote nodes
To add remote nodes to your network, use the script ``register_nodes.py``. To add nodes outside your LAN they will have to open ports.

Since miner nodes are busy mining, requests to these nodes might have a delayed response. The idea of a bookkeeping node is to keep track of the longest chain and resolve conflicts; it is this node that should be connected to the rest of the network and exchange information. It should look something like this:

```

        M       M
        |       |
        |       |
        ----B----
            |
            |      ----M
            |      |
            +------B
            |      |
            |      ----M
            |
        ----B----
        |       |
        |       |
        M       M
```
where `M` is a miner and `B` a bookkeeper, two miners and one bookkeeper for each node in this case.


