import socket
import struct
import time
from package.receiver import MulticastReceiver
from package.cache import Cache
from utils import xor

USER_ID = 1 # For the example
FILE_ID = 2 # For the example
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

    # Create a receiver object
    print(f"Creating multicast receiver with id={USER_ID} and requesting file {FILE_ID}...")
    receiver = MulticastReceiver(USER_ID, None)

    # Simulate the cache with received chunks
    print(f"Creating cache object for user with id={USER_ID} at user_{USER_ID}-file_{FILE_ID}.txt...")
    cache = Cache(f'user_{USER_ID}-file_{FILE_ID}.txt')

    # Receive cache data via unicast request
    print(f"Sending unicast request for cache for user with id={USER_ID} and updating user_{USER_ID}-file_{FILE_ID}.txt...")
    cache_data = receiver.send_unicast_request(UNICAST_SERVER_ADDRESS, FILE_ID)

    # Setting cache content
    cache.set_content(cache_data)

    # Setting cache to receiver
    receiver.set_cache(cache)

    time.sleep(1)  # Give the server some time to process the request

    print(f'Requested fileID: {FILE_ID}')
    print(f"User cache: {receiver.get_cache()}")
    
    received_packets = []
    while len(received_packets) < 10:
        data, _ = sock.recvfrom(1024)
        received_packets.append(data)

    print(f'Received packets: {received_packets}')
    
    ## TO DO ##
    ## DECODING HERE ##

    
    

if __name__ == "__main__":
    main()