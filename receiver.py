import argparse
import time
from package.receiver import MulticastReceiver
from package.cache import Cache

def main(args):
    
    USER_ID = args.receiver
    FILE_ID = args.request_content

    receiver = MulticastReceiver(args.sim_id, USER_ID, args.config, None)
    cache_file = f'server{USER_ID}-file_{FILE_ID}-test.txt'
    cache = Cache(cache_file)
    
    cache_data = receiver.send_unicast_request(FILE_ID)
    cache.set_content(cache_data)
    receiver.set_cache(cache)

    time.sleep(1)  
    
    receiver.start(FILE_ID)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='Light receiver',
                    description='Creates a a new receiver for Light communication.',
                    )
    parser.add_argument('receiver', help='The receiver ID.',  type=int)         # positional argument
    parser.add_argument('-rq', '--request_content', help='The requested content ID.',  type=int)      # option that takes a value
    parser.add_argument('-c', '--config', help='The config file associated with the receiver.', required=True, type=str)  # required option that takes a value
    parser.add_argument('-sim_id', '--sim_id', help='The simulation_id.', required=True, type=str)  # required option that takes a value

    main(parser.parse_args())