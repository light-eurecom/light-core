import json
import os
import socket
import struct
import time
import threading
from collections import defaultdict
from package.multicast_session import MulticastSession
from utils import encode_packet, file_exists, split_into_chunks, xor, logger

BUFFER_SIZE = 2048  # 1 MB buffer size

class MulticastServer:
    def __init__(self, multicast_group, files, receivers, cache_capacity, requested_files, nb_receivers):
        self.multicast_group = multicast_group
        self.files = files
        self.receivers = receivers
        self.session = MulticastSession(library=files, receivers=receivers, cache_capacity=cache_capacity)
        self.indices = self.session.get_chunks_indices()
        self.caches = self.session.get_indices_per_user_cache(self.indices)
        # self.chunked_files = self.split_chunks_videos()
        self.chunked_files = self.split_chunks()
        self.caches_with_files = defaultdict(dict)
        self.transmitted_packets = []
        self.requested_files = requested_files
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        ttl = struct.pack('b', 1)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        self.nb_receivers = nb_receivers
        
        
    def split_chunks(self):
        '''
        TODO: this works only in the files are (i) strings and (ii) of equal length and (iii) chunk size is not integer. We will need to generalize.
        '''
        
        # if len([1 for f in self.files if not isinstance(f, str)]) > 0 :
        #     raise Exception('At least one file is not of string type')
        # if len(set([len(f) for f in self.files])) > 1 :
        #     raise Exception('Files are not of the same size')
        # if not (len(self.files[0])/len(self.indices)).is_integer() :
        #     raise Exception('Chunk size is not integer')
        chunk_size = int(len(self.files[0]["value"]) / len(self.indices))
        splitted = dict()
        for f in self.files:
            splitted[f["id"]] = {ind: bytes(f["value"][i*chunk_size : (i+1)*chunk_size], 'utf-8') for i, ind in enumerate(self.indices)}

        return splitted
    
    def split_chunks_videos(self):
        '''
        '''
        splitted = dict()
        for f in self.files:
            list_of_chunks = self.split_video(f["compressed_path"])
            # splitted[f["id"]] = {ind: self.split_video(f["compressed_path"]) for i,ind in enumerate(self.indices)}
            splitted[f["id"]] = {ind: list_of_chunks[i] for i,ind in enumerate(self.indices)}

        return splitted
    
    def split_video(self, file_path):
        """Split the video into n equal-sized chunks."""
        try:
            video = open(file_path, 'rb')    
            video_size = os.path.getsize(file_path)
            chunk_size = int(video_size/len(self.indices))

            # Read and return video chunks
            chunks = []
            for _ in self.indices:
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
                self.caches_with_files[user][fileID] = {k: v for k, v in self.chunked_files[f["id"]].items() if k in self.caches[user]}
    
    def get_users_cache(self):
        return self.caches_with_files
    
    def generate_transmitted_packets(self):
        list_of_xor_packets = self.session.get_list_of_xor_packets_for_transmission(self.requested_files)
        self.transmitted_packets = []
        
        for _, xor_packet in enumerate(list_of_xor_packets):
            packet = None
            packet_obj = {}
            for j, fc in enumerate(xor_packet):
                try:
                    fileID = int(fc[0])-1  # Ensure fileID is an integer
                    chunkID = fc[1]
                    chunk = self.chunked_files[self.files[fileID]["id"]][chunkID]
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


    def send_packets(self):
            for packet in self.transmitted_packets:
                print(self.multicast_group)
                encoded_packet = encode_packet(packet)  # Encode the packet
                packet_bytes = json.dumps(encoded_packet).encode('utf-8')  # Serialize the encoded packet to bytes
                chunked_packets = split_into_chunks(packet_bytes, BUFFER_SIZE, last_packet=b"END_OF_CHUNK")

                for chunk in chunked_packets:
                    self.sock.sendto(chunk, self.multicast_group)
                    
            self.sock.sendto(b"LAST_PACKET", self.multicast_group)
            logger.success("Multicast transmission finished.")

    
    def update_requests(self):
        self.generate_transmitted_packets()
    
    def start(self, unicast_server):
        self.update_cache_with_files()
        threading.Thread(target=self.update_requests, args=()).start()
        
        if unicast_server:
            while True:
                if unicast_server.check_connections(self.nb_receivers):
                    logger.info(f"Starting on {self.multicast_group}")
                    time.sleep(5)
                    self.send_packets()
                    unicast_server.reset_connections()
                    break
        else:
            logger.info(f"Starting on {self.multicast_group}")
            self.send_packets()
