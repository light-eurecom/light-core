import threading
from package.multicast_server import MulticastServer
from package.unicast_server import UnicastServer
    
MULTICAST_GROUP = ('224.3.29.71', 10000)
    
def main():
    files = ['./data/video1.mp4',
             './data/video2.mp4', 
             './data/video3.mp4', 
             './data/video4.mp4', 
             './data/video5.mp4', 
             './data/video6.mp4', 
             './data/video7.mp4', 
             './data/video8.mp4', 
             './data/video9.mp4', 
             './data/video10.mp4']
    receivers = ['paul', 'anto', 'jony', 'elio', 'rony']
    requested_files = dict({1: 2, 2: 5, 3: 6, 4: 8, 5: 9})
    cache_capacity = 4

    
    multicast_server = MulticastServer(MULTICAST_GROUP, files, receivers, cache_capacity, requested_files)
    unicast_server = UnicastServer(users_cache=multicast_server.get_users_cache())
    threading.Thread(target=unicast_server.start).start()
    multicast_server.start(unicast_server)

if __name__ == "__main__":
    main()
