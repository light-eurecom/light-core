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

## What we've tried

Testing this multicast server setup across different network environments—ranging from a local machine network, to a home LAN, to an enterprise-scale LAN at the Eurecom lab—likely yielded varied results based on the complexity and capacity of each network.

### 1. **Local Machine Network**
This test involved running both the multicast server and receivers on the same machine, possibly simulating a simple local loopback scenario. The advantage here is that there are no external network factors like latency, packet loss, or routing issues. Everything is contained and controlled. The performance was probably excellent, with near-instant responses and smooth multicasting, given the absence of real network traffic. However, this setup doesn’t represent a real-world scenario, so it might not fully test the system’s robustness under actual network conditions.

### 2. **Local Home LAN**
Moving to a home LAN, with devices connected via a home router, introduces more realistic network conditions. A typical home LAN has moderate traffic, some interference, and less efficient routing than an enterprise-level network. You likely experienced a few minor issues, such as slight delays or packet losses, depending on the network quality and the number of devices using the router at the time. However, since home routers are generally built for reliable communication between devices, the multicast packets were probably transmitted efficiently most of the time, with occasional hiccups.

### 3. **Enterprise-Scale LAN (Eurecom Lab)**
The enterprise-scale LAN, such as the one in Eurecom’s lab, likely presented the most challenging environment for the multicast setup. These networks are designed for large-scale communication, with complex routing protocols, higher traffic loads, and sophisticated network management systems. Depending on the lab's specific network setup, you might have encountered challenges like network congestion, stricter security policies, or packet drops due to the sheer scale of communication happening simultaneously. While the multicast system may have worked, you likely faced some technical hurdles around packet handling and network tuning to optimize performance for such a large environment. Multicasting over this type of LAN can expose bottlenecks or inefficiencies in packet transmission that aren’t visible in smaller, simpler networks.

In summary, testing in each environment likely highlighted different strengths and weaknesses of your system. The local machine network was probably smooth but unrealistic, the home LAN introduced manageable real-world challenges, and the enterprise LAN revealed areas where further optimization might be needed.