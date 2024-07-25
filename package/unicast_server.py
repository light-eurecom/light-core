import socket
import time
import threading
from collections import defaultdict
from utils import logger, split_into_chunks

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
        logger.info("waiting 2s...")
        time.sleep(2)
        data = split_into_chunks(str(self.users_cache[user_id]), CHUNK_SIZE)
        i = 1
        for d in data:
            i = i +1
            logger.info("sending cache packet to receiver...")
            client_socket.sendall(str(d).encode('utf-8'))
            if(d == b'LAST_PACKET'):
                logger.success(f"{d}, {i} packets")
        client_socket.close()

    def start(self):
        logger.info(f"Unicast server listening on {self.host}:{self.port}")
        while True:
            client_socket, addr = self.server_socket.accept()
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_handler.start()