import base64
import json
import socket
import struct
from utils import xor, logger, decode_packet

BUFFER_SIZE = 2048
MULTICAST_GROUP = '224.0.0.1'
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
        
        cache = []
        while True:
            data = unicast_sock.recv(BUFFER_SIZE)
            if b'LAST_PACKET' in data:
                parts = data.split(b'LAST_PACKET', 1)
                if parts[0]:
                    cache.append(parts[0])
                logger.info("Received LAST_PACKET")
                break
            cache.append(data)
        
        unicast_sock.close()
        
        joined_bytes = b''.join(cache)  # Combine all byte sequences into one
        return  decode_packet(joined_bytes)  # Decode bytes to string
        
        
    def get_list_of_xor_packets(self, packets):
        extracted_indices = []
        
        for packet in packets:
            packet = decode_packet(packet)
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
    
    def save_video_file(self, file_path, data):
        """Save the video file."""
        with open(file_path, "wb") as file:
            file.write(data)
    
    def start(self, file_id):
        received_packets = []
        chunk = []
        while True:
            data, _ = self.sock.recvfrom(1024)
            if data == b"END_OF_CHUNK":
                received_packets.append(decode_packet(b''.join(chunk)))
                chunk = []
            elif data == b"LAST_PACKET":
                break
            else:
                chunk.append(data)
            
        list_of_xor_packets = self.get_list_of_xor_packets(received_packets)
        transmitted_packets = self.get_list_of_transmitted_packets(received_packets)
        indices = received_packets[0]["all_indices"]
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

        decoded_message = b""
        for ind in indices:
            if tuple(ind) in decoded_chunks:
                decoded_message += decoded_chunks[tuple(ind)]
            else:
                decoded_message += self.get_cache()[file_id][tuple(ind)]

        # Save the decoded message as a video file
        file_path = f"server{self.light_id}-video_{file_id}.mp4"
        self.save_video_file(file_path, decoded_message)
        logger.info(f"Successfully decoded and saved as: {file_path}")

        # Log the success message
        logger.success("Video file has been successfully saved.")
