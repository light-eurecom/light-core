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

The receiver sends a first packet, with content: 

```python
f"{self.light_id},{requested_fileID}"
```
So, if the receiver has ID 1 and requests file 2, the content will be:

```python
1,2
```
Receiving this, the server computes the cache that user 1 needs to have, and sends it as response to this unicast request. The format would be the following: 

```json
{1: {(1, 2): b'i', (1, 3): b'n', (1, 4): b's', (1, 5): b'u'}, 2: {(1, 2): b'a', (1, 3): b'b', (1, 4): b's', (1, 5): b'o'}, 3: {(1, 2): b'd', (1, 3): b'i', (1, 4): b'f', (1, 5): b'f'}, 4: {(1, 2): b'p', (1, 3): b'e', (1, 4): b'r', (1, 5): b'f'}, 5: {(1, 2): b'p', (1, 3): b'r', (1, 4): b'o', (1, 5): b'c'}, 6: {(1, 2): b'e', (1, 3): b'x', (1, 4): b'p', (1, 5): b'r'}, 7: {(1, 2): b'e', (1, 3): b's', (1, 4): b't', (1, 5): b'a'}, 8: {(1, 2): b'm', (1, 3): b'a', (1, 4): b'n', (1, 5): b'a'}, 9: {(1, 2): b'v', (1, 3): b'o', (1, 4): b'l', (1, 5): b'u'}, 10: {(1, 2): b'r', (1, 3): b'e', (1, 4): b'g', (1, 5): b'a'}}b'LAST_PACKET'
```

The last packet `b'LAST_PACKET'` indicates the end of a transmission. It's crucial when transferred data are huge, and need to be split into multiple chunks. 