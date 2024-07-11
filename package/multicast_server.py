import base64
import json
import socket
import struct
import time
import threading
from collections import defaultdict
from package.multicast_session import MulticastSession
from utils import xor

class MulticastServer:
    def __init__(self, multicast_group, files, receivers, cache_capacity):
        self.multicast_group = multicast_group
        self.files = files
        self.receivers = receivers
        self.session = MulticastSession(librairy=files, receivers=receivers, cache_capacity=cache_capacity)
        self.indices = self.session.get_chunks_indices()
        self.caches = self.session.get_indices_per_user_cache(self.indices)
        self.chunked_files = {f: {ind: bytes(f[i], 'utf-8') for i, ind in enumerate(self.indices)} for f in files}
        self.caches_with_files = defaultdict(dict)
        self.transmitted_packets = []
        self.requested_files = defaultdict(list)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        ttl = struct.pack('b', 1)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    
    def update_cache_with_files(self):
        for user in range(1, self.session.nb_receivers + 1):
            for i, f in enumerate(self.files):
                fileID = i + 1
                self.caches_with_files[user][fileID] = {k: v for k, v in self.chunked_files[f].items() if k in self.caches[user]}
    
    def get_users_cache(self):
        return self.caches_with_files
    
    def generate_transmitted_packets(self):
        list_of_xor_packets = self.session.get_list_of_xor_packets_for_transmission(self.requested_files)
        print("************************************")
        print(list_of_xor_packets)
        self.transmitted_packets = []
        for i, xor_packet in enumerate(list_of_xor_packets):
            packet = None
            packet_obj = {}
            for j, fc in enumerate(xor_packet):
                try:
                    fileID = int(fc[0]) - 1  # Ensure fileID is an integer
                    chunkID = fc[1]
                    chunk = self.chunked_files[self.files[fileID]][chunkID]
                    if j == 0:
                        packet = chunk
                    else:
                        packet = xor(packet, chunk)
                except (ValueError, KeyError, TypeError) as e:
                    print(f"Error processing packet: {e}")
                    continue
            packet_obj["indices"] = xor_packet
            packet_obj["value"] = packet    
            self.transmitted_packets.append(packet_obj)
        self.transmitted_packets[0]["all_indices"] = self.indices


    def encode_packet(self, packet):
        # Custom encoding function to handle bytes
        def encode_bytes(obj):
            if isinstance(obj, bytes):
                return base64.b64encode(obj).decode('utf-8')
            if isinstance(obj, tuple):
                return tuple(encode_bytes(item) for item in obj)
            if isinstance(obj, list):
                return [encode_bytes(item) for item in obj]
            if isinstance(obj, dict):
                return {key: encode_bytes(value) for key, value in obj.items()}
            return obj
        
        return encode_bytes(packet)

    def send_packets(self):
        while True:
            for packet in self.transmitted_packets:
                print(f'Sending packet: {packet}')
                encoded_packet = self.encode_packet(packet)  # Encode the packet
                packet_bytes = json.dumps(encoded_packet).encode('utf-8')  # Serialize the encoded packet to bytes
                self.sock.sendto(packet_bytes, self.multicast_group)
                time.sleep(0.1)
            print("Sending again in 8 seconds...")
            time.sleep(8)
    
    def update_requests(self, unicast_server):
        while True:
            time.sleep(5)  # Adjust as needed for how frequently to check for new requests
            if unicast_server.requests:
                self.requested_files = dict({1: 2, 2: 5, 3: 6, 4: 8, 5: 9})
                unicast_server.requests.clear()
                self.generate_transmitted_packets()
    
    def start(self, unicast_server):
        self.update_cache_with_files()
        threading.Thread(target=self.update_requests, args=(unicast_server,)).start()
        self.send_packets()
