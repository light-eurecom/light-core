import argparse
import base64
import json
import socket
import struct
import time
from package.receiver import MulticastReceiver
from package.cache import Cache
from utils import xor

MULTICAST_GROUP = '224.3.29.71'
SERVER_ADDRESS = ('', 10000)
UNICAST_SERVER_ADDRESS = ('localhost', 10001)


def decode_packet(packet):
        # Custom decoding function to handle base64 encoded strings
        def decode_bytes(obj):
            if isinstance(obj, str):
                try:
                    return base64.b64decode(obj)
                except Exception:
                    return obj  # Return the string if it's not a base64 encoded bytes object
            if isinstance(obj, tuple):
                return tuple(decode_bytes(item) for item in obj)
            if isinstance(obj, list):
                return [decode_bytes(item) for item in obj]
            if isinstance(obj, dict):
                return {key: decode_bytes(value) for key, value in obj.items()}
            return obj
        
        return decode_bytes(json.loads(packet))
    

def get_list_of_xor_packets(packets):
    extracted_indices = []
    for packet in packets:
        indices = packet['indices']
        formatted_indices = [(index, tuple(subindex)) for index, subindex in indices]
        extracted_indices.append(formatted_indices)
    return extracted_indices

def get_list_of_transmitted_packets(packets):
    extracted_values = []
    for packet in packets:
        value = packet['value']
        extracted_values.append(value)
    return extracted_values
        
def check_key_in_dict_items(dict_items, key):
    for item in dict_items:
        _, inner_dict = item
        if key in inner_dict:
            return True
    return False

def main(args):
    
    USER_ID = args.receiver
    FILE_ID = args.content
    
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

    # print(f'Requested fileID: {FILE_ID}')
    # print(f"User cache: {receiver.get_cache()}")
    
    received_packets = []
    while len(received_packets) < 10:
        data, _ = sock.recvfrom(1024)
        packet = data.decode('utf-8')
        decoded_packet = decode_packet(packet)
        received_packets.append(decoded_packet)
        

    # print(f'Received packets: {received_packets}')
    # print("Decoded packets for User 1 requesting File 2:")

    list_of_xor_packets = get_list_of_xor_packets(received_packets)
    transmitted_packets = get_list_of_transmitted_packets(received_packets)
    indices = received_packets[0]["all_indices"]
    # print(f"indices : {indices}")
    decoded_chunks = {}
    current_fileID = None
    current_chunkID = None
    for i, xor_packet in enumerate(list_of_xor_packets):
        packet = transmitted_packets[i]
        for fc in xor_packet:
            fileID = fc[0]
            chunkID = fc[1]
            if check_key_in_dict_items(receiver.get_cache().items(), chunkID):
                packet = xor(packet, receiver.get_cache()[fileID][chunkID])
            else:
                current_fileID = fileID
                current_chunkID = chunkID
        if current_fileID == FILE_ID:
            decoded_chunks[current_chunkID] = packet

    # print(f"User {USER_ID}: ")
    # print(f"\tDecoded chunks: {decoded_chunks}")

    decoded_message = ""
    for ind in indices:
        if tuple(ind) in decoded_chunks:
            decoded_message += decoded_chunks[tuple(ind)].decode('utf-8')
        else:
            decoded_message += receiver.get_cache()[FILE_ID][tuple(ind)].decode('utf-8')

    print(f"\tDecoded message: {decoded_message}")
    print()



    # Print the decoded message
    print(f"Decoded message for user {USER_ID}, file {FILE_ID}:")
    print(decoded_message)

    
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='Light receiver',
                    description='Createsa a new receiver for Light communication.',
                    epilog='Text at the bottom of help')
    parser.add_argument('receiver', help='The receiver ID.',  type=int)         # positional argument
    parser.add_argument('-c', '--content', help='The requested content ID.',  type=int)      # option that takes a value
    main(parser.parse_args())