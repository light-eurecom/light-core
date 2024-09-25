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


## Receiver

The code for the receiver can be found at `package/receiver.py`.

The receiver works in two main stages: **requesting** and **listening**.

1. **Requesting Content**: The process starts with the receiver sending a request to the server, asking for a specific piece of content, such as a video. This is done through a direct connection to the server, often using a technique called "unicast," where the receiver and server are in a one-to-one communication. In this request, the receiver tells the server exactly what content it wants.

2. **Listening for Multicast Content**: After the request is made, the server doesn't respond by sending the content back directly to the receiver over the same connection. Instead, it broadcasts the content in smaller pieces over a "multicast" channel. Multicast is like a radio or TV broadcast: the server sends out the content in such a way that multiple devices can "tune in" and receive it at the same time. This is more efficient than sending the content individually to each device.

   - The receiver is set up to listen to this broadcast. It knows which "channels" (called multicast groups) to tune into because the server provides this information when the request is made. 
   
   - As the server broadcasts the content in chunks (or pieces), the receiver gathers these pieces in the order they come. The process of collecting these chunks isn't always smooth—sometimes pieces might arrive out of order or some parts might be missing. 

3. **Assembling and Storing the Content**: As the receiver collects the pieces, it begins to assemble the full video. It also uses some advanced techniques to fill in any gaps or correct errors in the data it receives, ensuring the content is complete and accurate. 

4. **Saving the Video**: Once the receiver has all the chunks it needs, it combines them into a complete video file. This file is then saved locally on the receiver's system, ready for the user to play.

In summary, the receiver starts by sending a request to the server for a specific piece of content. Then, it listens to the server broadcasting that content over a network, gathers the pieces, assembles them into a full file, and finally saves it for the user to view. This method allows the server to efficiently share content with many receivers at once.


## Server

Here's the updated explanation, including the missing step:

1. **Knowing the Receivers**: The server starts by determining how many receivers it’s expecting. It waits for each of them to connect and send a signal that they’re ready.

2. **Waiting for Requests**: Each receiver sends a unicast request to the server, like saying, "I'm ready for my content." The server waits until every expected receiver has sent their request before moving forward.

3. **Preparing Caches**: Once all the requests are in, the server prepares **caches** for each receiver. These caches contain important information, like special data or packets related to the video the receiver is going to assemble. It ensures that every receiver gets a customized set of information.

4. **Sending Cache Responses**: The server then responds to each receiver by sending them their specific cache. These caches will help the receivers piece together the video later on.

5. **Preparing Multicast Packets**: After sending the cache responses, the server prepares the packets that it will multicast. These packets are based on the video but are specially crafted to be used alongside the caches the receivers already have.

6. **Broadcasting the Prepared Packets**: Once the packets are ready, the server multicasts them to all the receivers at the same time. Using both the prepared multicast packets and their individual caches, the receivers can reconstruct the full content.

So, the server goes through a process of waiting for requests, preparing caches, creating special multicast packets, and then sending everything needed for the receivers to assemble the video content.


- describe the files/repos in git (configs...)
"""
main fonct of receiver : 
- receiver requests...
- store in memo...
...
"""

describe the experiments(same machine, same lan...) + what we tried 

8:30 thrusday Pavlos