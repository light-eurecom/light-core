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

#### Unicast data packet format

```
# request
{receiver_id}-{file_id}
# ex: 1-2

# response
# the corresponding cache is sent under the following format:

{1: {(1, 2): b'i', (1, 3): b'n', (1, 4): b's', (1, 5): b'u'},
2: {(1, 2): b'a', (1, 3): b'b', (1, 4): b's', (1, 5): b'o'},
...
n-1: {(1, 2): b'v', (1, 3): b'o', (1, 4): b'l', (1, 5): b'u'},
n: {(1, 2): b'r', (1, 3): b'e', (1, 4): b'g', (1, 5): b'a'}}

# This is just an example
```



