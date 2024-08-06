# Light core

Here are the algorithms for the light core mechanism. 

## Intitiation

Create a virtual environment and install packages: 

```bash
virtualenv env && source env/bin/activate
pip3 install -r requirements.txt
```

## Start server

```bash
python3 server.py
```

## Start receiver

The receiver takes the ID of the receiver as input as well as the ID of the requested file. 

```
python3 receiver.py -h

usage: Light receiver [-h] [-c CONTENT] receiver

Createsa a new receiver for Light communication.

positional arguments:
  receiver              The receiver ID.

options:
  -h, --help            show this help message and exit
  -c CONTENT, --content CONTENT
                        The requested content ID.
```

Example, with user 1 requesting file 2:

```bash
python3 receiver.py 1 -c 2
```

## Transmission flow

Here is how a communication works:

1. You start the server, indicating how many receivers it expects. It then waits for each receivers to ask for their cache before starting multicast
2. The server serves each receiver with their respecting caches, over unicast. 
3. When all receivers have been served, the multicast can start
4. When all multicast packets have been sent, the communication ends

### Packet format

The transmission uses JSON format. 
Each multicast communcation consists of:

- Data packets, the first packet also containing "all_indices" field, needed to decrypt the overall packets. 
- A last packet, simple as "LAST_PACKET"

Here would be a basic communication:

