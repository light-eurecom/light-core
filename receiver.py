import socket
import struct
import time
from collections import defaultdict
from package.receiver import MulticastReceiver
from package.cache import Cache
from utils import xor

USER_ID = 4  # Or light_id basically
FILE_ID = 8  # The requested file id
MULTICAST_GROUP = '224.3.29.71'
SERVER_ADDRESS = ('', 10000)
UNICAST_SERVER_ADDRESS = ('localhost', 10001)

def main():
    # Set up the socket for multicast reception
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(SERVER_ADDRESS)

    # Join multicast group
    group = socket.inet_aton(MULTICAST_GROUP)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    # Create new receiver object
    receiver = MulticastReceiver(USER_ID, None)
    # This part could be done inside Receiver object but we do it here for now, more explicit
    cache = Cache(f'user_{USER_ID}-file_{FILE_ID}.txt')
    # Receive cache data via unicast request
    cache_data = receiver.send_unicast_request(UNICAST_SERVER_ADDRESS, FILE_ID)
    # Setting cache content
    cache.set_content(cache_data)
    # Setting cache to receiver
    receiver.set_cache(cache)

    time.sleep(1)  # Give the server some time to process the request

    print(f'Requested fileID: {FILE_ID}')
    print(f"User cache: {receiver.get_cache()}")
    print(f"User cache type: {type(receiver.get_cache())}")

    packets = []
    while len(packets) < 10:
        data, _ = sock.recvfrom(1024)
        packets.append(data)
    print(f'Received packets: {packets}')

    # Decode packets for user 4
    requested_fileID = FILE_ID
    decoded_chunks = {}
    current_fileID = None
    current_chunkID = None

    for _, packet in enumerate(packets):
        for _, chunks in receiver.get_cache().items():
            for chunkID, chunk in chunks.items():
                    packet = xor(packet, chunk)
            
            current_chunkID = chunkID
            decoded_chunks[current_chunkID] = packet

    print(f"User {receiver.light_id}: ")
    print(f"\tDecoded chunks: {decoded_chunks}")

    decoded_message = ""
    indices = list(range(10))  # Assuming indices are 0-9, update as necessary
    for ind in indices:
        if ind in decoded_chunks:
            decoded_message += decoded_chunks[ind].decode('utf-8')
        elif ind in receiver.get_cache().get(requested_fileID, {}):
            decoded_message += receiver.get_cache()[requested_fileID][ind].decode('utf-8')
        else:
            decoded_message += '?'

    print(f"\tDecoded message: {decoded_message}")

if __name__ == "__main__":
    main()
