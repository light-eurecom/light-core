import base64
import json
import os
import socket
import struct
import time
import threading
from collections import defaultdict
from package.multicast_session import MulticastSession
from utils import xor, logger

class MulticastServer:
    def __init__(self, multicast_group, files, receivers, cache_capacity, requested_files):
        self.multicast_group = multicast_group
        self.files = files
        self.receivers = receivers
        self.session = MulticastSession(librairy=files, receivers=receivers, cache_capacity=cache_capacity)
        self.indices = self.session.get_chunks_indices()
        self.caches = self.session.get_indices_per_user_cache(self.indices)
        self.chunked_files = self.split_chunks()
        self.caches_with_files = defaultdict(dict)
        self.transmitted_packets = []
        self.requested_files = requested_files
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        ttl = struct.pack('b', 1)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        
    def split_chunks(self):
        '''
        TODO: this works only in the files are (i) strings and (ii) of equal length and (iii) chunk size is not integer. We will need to generalize.
        '''
        
        if len([1 for f in self.files if not isinstance(f, str)]) > 0 :
            raise Exception('At least one file is not of string type')
        # if len(set([len(f) for f in self.files])) > 1 :
        #     raise Exception('Files are not of the same size')
        # if not (len(self.files[0])/len(self.indices)).is_integer() :
        #     raise Exception('Chunk size is not integer')
        chunk_size = int(len(self.files[0])/len(self.indices))

        splitted = dict()
        for f in self.files:
            splitted[f] = {ind: bytes(f[i*chunk_size : (i+1)*chunk_size], 'utf-8') for i,ind in enumerate(self.indices)}

        return splitted
    
    def split_chunks_V2(self):
        '''
        TODO: this works only in the files are (i) strings and (ii) of equal length and (iii) chunk size is not integer. We will need to generalize.
        '''
        
        if len([1 for f in self.files if not isinstance(f, str)]) > 0 :
            raise Exception('At least one file is not of string type')
        if len(set([len(f) for f in self.files])) > 1 :
            raise Exception('Files are not of the same size')
        if not (len(self.files[0])/len(self.indices)).is_integer() :
            raise Exception('Chunk size is not integer')
        chunk_size = int(len(self.files[0])/len(self.indices))

        splitted = dict()
        for f in self.files:
            splitted[f] = {ind: self.split_video(f) for i,ind in enumerate(self.indices)}

        return splitted
    
    def split_video(self, file_path):
        """Split the video into n equal-sized chunks."""
        try:
            print(file_path)
            video = open(file_path, 'rb')
            video_size = os.path.getsize(file_path)
            chunk_size = int(len(video_size)/len(self.indices))

            # Read and return video chunks
            chunks = []
            for _ in range(self.indices):
                chunk = video.read(chunk_size)
                chunks.append(chunk)

            video.close()

            return chunks

        except Exception as e:
            print("[Error] Unable to split video:", str(e))
            return None

    def update_cache_with_files(self):
        for user in range(1, self.session.nb_receivers + 1):
            for i, f in enumerate(self.files):
                fileID = i + 1
                self.caches_with_files[user][fileID] = {k: v for k, v in self.chunked_files[f].items() if k in self.caches[user]}
    
    def get_users_cache(self):
        return self.caches_with_files
    
    def generate_transmitted_packets(self):
        list_of_xor_packets = self.session.get_list_of_xor_packets_for_transmission(self.requested_files)
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
                    logger.error(f"Error processing packet: {e}")
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
                logger.info(f'Sending packet: {packet}')
                encoded_packet = self.encode_packet(packet)  # Encode the packet
                packet_bytes = json.dumps(encoded_packet).encode('utf-8')  # Serialize the encoded packet to bytes
                self.sock.sendto(packet_bytes, self.multicast_group)
                time.sleep(0.1)
            logger.info(f'Sending last packet...')
            self.sock.sendto(b"LAST_PACKET", self.multicast_group)
            logger.info("Sending again in 8 seconds...")
            time.sleep(8)
    
    def update_requests(self, unicast_server):
        while True:
            time.sleep(5)  # Adjust as needed for how frequently to check for new requests
            if unicast_server.requests:
                unicast_server.requests.clear()
                self.generate_transmitted_packets()
    
    def start(self, unicast_server):
        self.update_cache_with_files()
        threading.Thread(target=self.update_requests, args=(unicast_server,)).start()
        self.send_packets()
