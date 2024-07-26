import json
import socket
import time
import threading
from collections import defaultdict
from utils import logger, split_into_chunks, encode_packet

CHUNK_SIZE = 2048

class UnicastServer:
    def __init__(self, users_cache, host='localhost', port=10001):
        self.host = host
        self.port = port
        self.users_cache = users_cache
        self.requests = defaultdict(list)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
    
    def handle_client(self, client_socket):
        request = client_socket.recv(1024).decode('utf-8')
        user_id, file_id = map(int, request.split(','))
        self.requests[user_id].append(file_id)
        time.sleep(2)
        
        encoded_cache = encode_packet(self.users_cache[user_id])
        cache = json.dumps(encoded_cache).encode('utf-8')
                
        data = split_into_chunks(cache, CHUNK_SIZE)
        logger.info("sending cache packets to receiver...")
        for d in data:
            client_socket.sendall(d)
            if(d == b'LAST_PACKET'):
                logger.success(f"Send cache to {user_id}.")
        client_socket.close()

    def start(self):
        logger.info(f"Unicast server listening on {self.host}:{self.port}")
        while True:
            client_socket, addr = self.server_socket.accept()
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_handler.start()