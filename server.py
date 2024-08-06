import argparse
import json
import threading
from package.multicast_server import MulticastServer
from package.unicast_server import UnicastServer
from utils import logger, read_config

def main(args):
    try:
        config = read_config(args.config)
        multicast_groups = config['MULTICAST_GROUPS']
        library_file = config['LIBRARY_FILE']
        
        with open(library_file, 'r') as file:
            library = json.load(file)
            files = library['files']
    except Exception as e: 
        logger.error(e)
        return
    
    receivers = ['paul', 'anto', 'jony', 'elio', 'rony']
    requested_files = dict({1: 2, 2: 5, 3: 6, 4: 8, 5: 9})
    cache_capacity = 4

    multicast_server = MulticastServer(multicast_groups[0], files, receivers, cache_capacity, requested_files, args.nb_receivers)
    unicast_server = UnicastServer(users_cache=multicast_server.get_users_cache())
    threading.Thread(target=unicast_server.start).start()
    multicast_server.start(unicast_server)
    
    for i in range(multicast_groups):
        if i != 0:
            logger.info(f"Starting mutlicast on {multicast_groups[i]}")
            multicast_server = MulticastServer(multicast_groups[i], files, receivers, cache_capacity, requested_files, args.nb_receivers)
            multicast_server.start(unicast_server=None)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='Light server',
                    description='Creates a new server for Light communication.',
                    )
    parser.add_argument('nb_receivers', help='The number of expected receivers.',  type=int)  # positional argument
    parser.add_argument('-c', '--config', help='The config file associated with the server.', required=True, type=str)  # required option that takes a value

    main(parser.parse_args())
