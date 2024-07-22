import argparse
import time
from package.receiver import MulticastReceiver
from package.cache import Cache

def main(args):
    
    USER_ID = args.receiver
    FILE_ID = args.content

    receiver = MulticastReceiver(USER_ID, None)
    cache_file = f'server{USER_ID}-file_{FILE_ID}.txt'
    cache = Cache(cache_file)
    
    cache_data = receiver.send_unicast_request(FILE_ID)
    cache.set_content(cache_data)
    receiver.set_cache(cache)

    time.sleep(1)  
    
    receiver.start(FILE_ID)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='Light receiver',
                    description='Createsa a new receiver for Light communication.',
                    )
    parser.add_argument('receiver', help='The receiver ID.',  type=int)         # positional argument
    parser.add_argument('-c', '--content', help='The requested content ID.',  type=int)      # option that takes a value
    main(parser.parse_args())