import base64
import json
import socket
import struct
from utils import xor, logger


BUFFER_SIZE = 4096
MULTICAST_GROUP = '224.3.29.71'
SERVER_ADDRESS = ('', 10000)
UNICAST_SERVER_ADDRESS = ('localhost', 10001)

class MulticastReceiver:
    def __init__(self, light_id, cache=None):
        self.light_id = light_id
        self.cache = cache
        self.list_of_xor_packets = []
        self.indices = []  # Assuming this is needed for decoding
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(SERVER_ADDRESS)

        group = socket.inet_aton(MULTICAST_GROUP)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    def set_list_of_xor_packets(self, packets):
        self.list_of_xor_packets = packets
        self.indices = [i for packet in packets for i in packet]
        
    def get_cache(self):
        return self.cache.get_content()

    def set_cache(self, cache):
        self.cache = cache
    
    def send_unicast_request(self, requested_fileID):
        unicast_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        unicast_sock.connect(UNICAST_SERVER_ADDRESS)
        request_message = f"{self.light_id},{requested_fileID}"
        unicast_sock.sendall(request_message.encode('utf-8'))
        
        response = unicast_sock.recv(BUFFER_SIZE)
        cache_data = str(response.decode('utf-8'))
        unicast_sock.close()
        return cache_data
    
    def decode_packet(self, packet):
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
    
    def get_list_of_xor_packets(self, packets):
        extracted_indices = []
        for packet in packets:
            indices = packet['indices']
            formatted_indices = [(index, tuple(subindex)) for index, subindex in indices]
            extracted_indices.append(formatted_indices)
        return extracted_indices

    def get_list_of_transmitted_packets(self, packets):
        extracted_values = []
        for packet in packets:
            value = packet['value']
            extracted_values.append(value)
        return extracted_values
    
    def check_key_in_dict_items(self, dict_items, key):
        for item in dict_items:
            _, inner_dict = item
            if key in inner_dict:
                return True
        return False
    
    def start(self, file_id):
        received_packets = []
        while True: ## @TODO@ : this is hard coded. Needs to change to handle generic lenghts (e.g., the server could send sth like "last message", similarly to the initial demo we've implemented)
            data, _ = self.sock.recvfrom(1024)
            packet = data.decode('utf-8')
            if packet == "LAST_PACKET":
                break
            decoded_packet = self.decode_packet(packet)
            received_packets.append(decoded_packet)
            
            
        ## @@TODO@@ the following functionality up to line 127, should be implemented in a method. In fact it decodes and puts in order the packets of the file
        list_of_xor_packets = self.get_list_of_xor_packets(received_packets)
        transmitted_packets = self.get_list_of_transmitted_packets(received_packets)
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
                if self.check_key_in_dict_items(self.get_cache().items(), chunkID):
                    packet = xor(packet, self.get_cache()[fileID][chunkID])
                else:
                    current_fileID = fileID
                    current_chunkID = chunkID
            if current_fileID == file_id:
                decoded_chunks[current_chunkID] = packet

        decoded_message = ""
        for ind in indices:
            if tuple(ind) in decoded_chunks:
                decoded_message += decoded_chunks[tuple(ind)].decode('utf-8')
            else:
                decoded_message += self.get_cache()[file_id][tuple(ind)].decode('utf-8')


        # Print the decoded message
        logger.info(f"Decoded message for user {self.light_id}, file {file_id}:")
        logger.success(decoded_message)


