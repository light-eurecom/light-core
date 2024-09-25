import json
import os
import socket
import struct
import subprocess
import time
from package.logger_manager import LoggerManager
from common.utils import custom_logger, xor, decode_packet, get_unicast_address
from common.config import SIMULATION_OUTPUT_PATH, UNICAST_PORT
BUFFER_SIZE = 1024
SERVER_ADDRESS = ('', 10000)

class MulticastReceiver:
    def __init__(self, sim_id, light_id, config_file, cache=None):
        self.sim_id = sim_id
        self.logger_manager = LoggerManager(sim_id)
        self.light_id = light_id
        self.cache = cache
        self.list_of_xor_packets = []
        self.indices = []  # Assuming this is needed for decoding
        self.socks = []  # List of sockets for different multicast groups
        self.unicast_server_address = (get_unicast_address(config_file), UNICAST_PORT)


    def set_list_of_xor_packets(self, packets):
        self.list_of_xor_packets = packets
        self.indices = [i for packet in packets for i in packet]
        
    def get_cache(self):
        return self.cache.get_content()

    def set_cache(self, cache):
        self.cache = cache
    
    def send_unicast_request(self, requested_fileID):
        try:
            unicast_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            unicast_sock.connect(self.unicast_server_address)
            request_message = f"{self.light_id},{requested_fileID}"
            unicast_sock.sendall(request_message.encode('utf-8'))
            
            cache = []
            first_packet_received = False  # Flag to track the first packet
            
            while True:
                data = unicast_sock.recv(BUFFER_SIZE)
                
                if not first_packet_received:
                    # Skip the first packet
                    first_packet_received = True
                    self.multicast_addresses = json.loads(data.decode("utf-8"))
                    continue
                
                if b'LAST_PACKET' in data:
                    parts = data.split(b'LAST_PACKET', 1)
                    if parts[0]:
                        cache.append(parts[0])
                    self.logger_manager.update("logs", "Received LAST_PACKET", append=True)
                    custom_logger("Received LAST_PACKET", level="info")
                    break
                
                cache.append(data)
            
            unicast_sock.close()
            
            joined_bytes = b''.join(cache)  # Combine all byte sequences into one
            return decode_packet(joined_bytes)  # Decode bytes to string
        
        except Exception as e:
            custom_logger(f"Unicast server seems down. Exiting: {e}", level="error")
            exit()

        
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
            
    def join_multicast_group(self, multicast_group, index: int):
        port = 10000 + index
        print(f"{multicast_group}:{port}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        
        # Bind to the interface address, not the multicast address
        sock.bind(('', port))  # Bind to all interfaces on the given port

        group = socket.inet_aton(multicast_group)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.socks.append(sock)

    def open_video_with_vlc(self, file_path):
        """Open the video file with VLC media player."""
        try:
            # Adjust the command based on your OS
            if os.name == 'posix':  # Unix-like (Linux, macOS)
                try:
                    subprocess.run(['vlc', file_path])
                except Exception as e:
                   subprocess.run(['/Applications/VLC.app/Contents/MacOS/VLC', file_path]) 
            elif os.name == 'nt':  # Windows
                subprocess.run(['C:\\Program Files\\VideoLAN\\VLC\\vlc.exe', file_path])
            else:
                custom_logger(f"Failed to open VLC", level="error")
        except Exception as e:
            custom_logger(f"Failed to open VLC: {e}", level="error")


    def start(self, file_id):
        decoded_message = b""
        index = 0
        
        for address in self.multicast_addresses:
            self.join_multicast_group(address, index)
            index += 1
            received_packets = []
            chunks = {sock: [] for sock in self.socks}
            
            while True:
                for sock in list(self.socks):
                    try:
                        sock.settimeout(5)
                        data, _ = sock.recvfrom(1024)
                        
                        if data == b"END_OF_CHUNK":
                            received_packets.append(decode_packet(b''.join(chunks[sock])))
                            chunks[sock] = []
                        elif data == b"LAST_PACKET":
                            self.socks.remove(sock)
                            sock.close() 
                            break
                        else:
                            chunks[sock].append(data)
                    
                    except socket.timeout:
                        custom_logger(f"Timeout on socket {sock}, continuing...", level="warning")
                        continue
                
                if not self.socks:
                    break

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

            for ind in indices:
                if tuple(ind) in decoded_chunks:
                    decoded_message += decoded_chunks[tuple(ind)]
                else:
                    decoded_message += self.get_cache()[file_id][tuple(ind)]

            file_path = os.path.join(SIMULATION_OUTPUT_PATH, f"{self.sim_id}-server{self.light_id}-video_{file_id}.mp4")
            self.save_video_file(file_path, decoded_message)
            video_size = os.path.getsize(file_path)
            custom_logger(f"video size : {video_size}", level="success")
            # logger.info(f"Successfully decoded and saved as: {file_path}. Opening with VLC...")
            # self.open_video_with_vlc(file_path)

            # Log the success message
            custom_logger("Video file has been successfully saved.", level="finished")
