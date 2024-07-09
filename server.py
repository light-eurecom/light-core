import threading
from package.multicast_server import MulticastServer
from package.unicast_server import UnicastServer
from utils import xor

def main():
    files = ['alleviated', 'adulterate', 'bookkeeper', 'chromosome', 'calculated', 'determined', 'excavation', 'formidable', 'graciously', 'hypnotized']
    receivers = ['paul', 'anto', 'jony', 'elio', 'rony']
    multicast_group = ('224.3.29.71', 10000)
    cache_capacity = 4

    
    multicast_server = MulticastServer(multicast_group, files, receivers, cache_capacity)
    unicast_server = UnicastServer(users_cache=multicast_server.get_users_cache())
    threading.Thread(target=unicast_server.start).start()
    multicast_server.start(unicast_server)

if __name__ == "__main__":
    main()
