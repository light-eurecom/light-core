import argparse
import json
import threading
import time
from package.multicast_server import MulticastServer
from package.unicast_server import UnicastServer
from common.utils import custom_logger, read_config

def main(args):
    try:
        config = read_config(args.config)
        multicast_groups = config['MULTICAST_GROUPS']
        library_file = config['LIBRARY_FILE']
        print(library_file)
        with open(library_file, 'r') as file:
            library = json.load(file)
            files = library['files']
    except Exception as e: 
        custom_logger(message=e, level='error')
        return
    
    receivers = ['paul', 'anto', 'jony', 'elio', 'rony']
    requested_files = dict({1: 2, 2: 5, 3: 6, 4: 8, 5: 9})
    cache_capacity = 4
    
    

    for i in range(len(multicast_groups)):
        group = multicast_groups[i]
        # custom_logger(f"Starting mutlicast on {str(group)}", level="info")
        if i == 0:
            multicast_server = MulticastServer(args.sim_id, group, files, receivers, cache_capacity, requested_files, args.nb_receivers)
            unicast_server = UnicastServer(args.sim_id, users_cache=multicast_server.get_users_cache(), config_file=args.config)
            threading.Thread(target=unicast_server.start).start()
            multicast_server.start(unicast_server)
        else:
            multicast_server = MulticastServer(args.sim_id, group, files, receivers, cache_capacity, requested_files, args.nb_receivers)
            multicast_server.start(unicast_server=None)
        time.sleep(5)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='Light server',
                    description='Creates a new server for Light communication.',
                    )
    parser.add_argument('nb_receivers', help='The number of expected receivers.',  type=int)  # positional argument
    parser.add_argument('-c', '--config', help='The config file associated with the server.', required=True, type=str)  # required option that takes a value
    parser.add_argument('-sim_id', '--sim_id', help='The simulation_id.', required=True, type=str)  # required option that takes a value

    main(parser.parse_args())
