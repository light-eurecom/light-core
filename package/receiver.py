import socket

class MulticastReceiver:
    def __init__(self, light_id, cache=None):
        self.light_id = light_id
        self.cache = cache
        self.list_of_xor_packets = []
        self.indices = []  # Assuming this is needed for decoding

    def set_list_of_xor_packets(self, packets):
        self.list_of_xor_packets = packets
        self.indices = [i for packet in packets for i in packet]
        
    def get_cache(self):
        return self.cache.get_content()

    def set_cache(self, cache):
        self.cache = cache
    
    def send_unicast_request(self, server_address, requested_fileID):
        unicast_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        unicast_sock.connect(server_address)
        request_message = f"{self.light_id},{requested_fileID}"
        unicast_sock.sendall(request_message.encode('utf-8'))
        
        response = unicast_sock.recv(4096)
        cache_data = str(response.decode('utf-8'))
        unicast_sock.close()
        return cache_data

