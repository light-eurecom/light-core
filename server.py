import argparse
import json
import os
import threading
from package.multicast_server import MulticastServer
from package.unicast_server import UnicastServer
from package.video_formatter import VideoFormatter
from utils import logger

MULTICAST_GROUP = ('224.0.0.1', 10000)
LIBRARY_FILE = 'library.json'
FORMATTED_VIDEOS_FOLDER = "./compressed_videos"

def folder_exists(folder_path):
    """
    Checks if the folder exists.

    :param folder_path: Path to the folder
    :return: True if folder exists, False otherwise
    """
    return os.path.exists(folder_path) and os.path.isdir(folder_path)
    
def is_folder_empty(folder_path):
    """
    Checks if the folder is empty.

    :param folder_path: Path to the folder
    :return: True if folder is empty, False otherwise
    """
    if not folder_exists(folder_path):
        raise FileNotFoundError(f"The folder at {folder_path} does not exist or is not a directory.")
    
    return len(os.listdir(folder_path)) == 0


def main(args):
    try:
        with open(LIBRARY_FILE, 'r') as file:
            library = json.load(file)
            files = library['files']
    except Exception as e: 
        logger.error(e)
        return
    
    receivers = ['paul', 'anto', 'jony', 'elio', 'rony']
    requested_files = dict({1: 2, 2: 5, 3: 6, 4: 8, 5: 9})
    cache_capacity = 4

    multicast_server = MulticastServer(MULTICAST_GROUP, files, receivers, cache_capacity, requested_files, args.nb_receivers)
    unicast_server = UnicastServer(users_cache=multicast_server.get_users_cache())
    threading.Thread(target=unicast_server.start).start()
    multicast_server.start(unicast_server)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='Light server',
                    description='Creates a a new server for Light communication.',
                    )
    parser.add_argument('nb_receivers', help='The number of expected receivers.',  type=int)         # positional argument
    main(parser.parse_args())
