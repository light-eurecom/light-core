import base64
import configparser
import json
import os
import time
from loguru import logger # type: ignore
import gzip
import io
from common.config import SIMULATION_OUTPUT_PATH, DATA_PATH


logger.remove()  # Remove the default configuration (file handler)
logger.add(lambda msg: print(msg, end=''), colorize=True, format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>", level="INFO", diagnose=False)


def custom_logger(message, level="INFO"):
    print(f"{level.upper()}:{message}")

logger.remove()
xor = lambda x, y: bytes(i ^ j for i, j in zip(x, y))


def compress_chunk(chunk):
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb') as f:
        f.write(chunk)
    return buffer.getvalue()


def split_into_chunks(data, chunk_size, last_packet=b"LAST_PACKET"):
    """Split data into chunks of specified size."""
    res = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
    res.append(last_packet)
    return res

def encode_packet(packet):
        # Custom encoding function to handle bytes
        def encode_bytes(obj):
            if isinstance(obj, bytes):
                return base64.b64encode(obj).decode('utf-8')
            if isinstance(obj, tuple):
                return tuple(encode_bytes(item) for item in obj)
            if isinstance(obj, list):
                return [encode_bytes(item) for item in obj]
            if isinstance(obj, dict):
                return {str(key): encode_bytes(value) for key, value in obj.items()}
            return obj
        
        return encode_bytes(packet)
    

def decode_packet(packet):
    def decode_bytes(obj):
        if isinstance(obj, str):
            try:
                # Try to decode base64 encoded strings
                return base64.b64decode(obj)
            except Exception:
                # Return as is if decoding fails
                return obj
        elif isinstance(obj, bytes):
            return obj
        elif isinstance(obj, tuple):
            return tuple(decode_bytes(item) for item in obj)
        elif isinstance(obj, list):
            return [decode_bytes(item) for item in obj]
        elif isinstance(obj, dict):
            new_dict = {}
            for key, value in obj.items():
                # Convert string keys to integer keys where possible
                try:
                    new_key = int(key)  # Try to convert key to integer
                except ValueError:
                    # Handle keys that are tuples represented as strings
                    try:
                        new_key = eval(key)  # Convert string representation of tuple to tuple
                        if not isinstance(new_key, tuple):
                            new_key = key  # If conversion fails, keep original key
                    except (SyntaxError, NameError):
                        new_key = key  # Keep key as is if conversion fails
                new_dict[new_key] = decode_bytes(value)
            return new_dict
        else:
            return obj

    try:
        if isinstance(packet, (str, bytes)):
            packet = json.loads(packet)
        return decode_bytes(packet)
    except Exception as e:
        logger.error(e)
        return None
    
    
    
def folder_exists(folder_path):
    """
    Checks if the folder exists.

    :param folder_path: Path to the folder
    :return: True if folder exists, False otherwise
    """
    return os.path.exists(folder_path) and os.path.isdir(folder_path)

def file_exists(file_path):
    """
    Checks if the file exists.

    :param file_path: Path to the file
    :return: True if file exists, False otherwise
    """
    return os.path.exists(file_path)
    
def is_folder_empty(folder_path):
    """
    Checks if the folder is empty.

    :param folder_path: Path to the folder
    :return: True if folder is empty, False otherwise
    """
    if not folder_exists(folder_path):
        raise FileNotFoundError(f"The folder at {folder_path} does not exist or is not a directory.")
    
    return len(os.listdir(folder_path)) == 0

def read_config(config_file):
    """
    Reads the configuration file and returns the config dictionary.

    :param config_file: Path to the configuration file
    :return: Configuration dictionary
    """
    config = configparser.ConfigParser()
    try:
        config.read(config_file)
        groups = []
        i = 0
        for group in json.loads(config.get('server', 'multicast_groups')):
            multicast_group = (group, 10000 + i)
            groups.append(multicast_group)
            i = i +1
        library_file = config.get('server', 'library_file')
        return {'MULTICAST_GROUPS': groups, 'LIBRARY_FILE': library_file}
    except Exception as e:
        logger.error(f"Error reading config file {config_file}: {e}")
        raise

def get_multicast_addresses(config_file):
    """
    Reads the configuration file and returns only the multicast addresses.

    :param config_file: Path to the configuration file
    :return: the multicast addresses as list
    """
    config = configparser.ConfigParser()
    try:
        config.read(config_file)
        groups = []
        for group in json.loads(config.get('server', 'multicast_groups')):
            groups.append(group)
        return groups
    except Exception as e:
        logger.error(f"Error reading config file {config_file}: {e}")
        raise
    
def get_unicast_address(config_file):
    """
    Reads the configuration file and returns only the unicast address.

    :param config_file: Path to the configuration file
    :return: the unicast address as str
    """

    try:
        # Read the config file
        config = configparser.ConfigParser()
        config.read(config_file)
        # Access the unicast address
        return str(config.get('unicast_server', 'unicast_ip'))
    except Exception as e:
        logger.error(f"Error reading config file {config_file}: {e}")
        raise
    
def create_simulation_schema(nb_receivers, nb_routers):
    simulation_id = f"sim_{int(time.time())}"
    file_path = os.path.join(SIMULATION_OUTPUT_PATH, f'{simulation_id}.json')
    print(file_path)
    # Load the base JSON
    with open(os.path.join(DATA_PATH, "demos.json"), 'r') as file:
        base = json.load(file)[0]
    
    # Initialize the new data based on the base structure
    data = base.copy()
    data["id"] = simulation_id
    data["status"] = "pending" 
    data["logs"] = []
    data["default_setup"]["name"] = f"Basic XOR - {nb_receivers} receivers"
    data["nb_receivers"] = nb_receivers
    data["nb_routers"] = nb_routers
    data["routers"] = []
    data["default_setup"]["nodes"] = []
    data["default_setup"]["edges"] = []
    data["steps"]=  [{
            "content": "Basic example: An origin server stores in its DB and serves a catalog of files (here: files correspond to well known quotes).",
            "target": ".demo_origin_server",
            "disableBeacon": True
        },
        {
            "content": "The edge servers have a cache with storage capacity of 1 file. However, they do not store 1 entire file, but they store 2 parts of 2 files (different parts at each edge server).",
            "target": ".receiver-1"
        },
        {
            "content": "Edge servers 1 and 2 request different files: 'All you need is love.' and 'I think, therefore I am.' respectively.",
            "target": ".receiver-2"
        },
        {
            "content": "The origin server receives the requests and proceeds with the response process.",
            "target": ".demo_origin_server"
        },
        {
            "content": "The origin server combines the 2nd part of the 1st file and the 1st part of the 2nd file, and sends the coded message; in total, it sends a message of size 50% of a file.",
            "target": ".demo_origin_server"
        },
        {
            "content": "The origin server sends the coded message (50% of file size) to the edge servers as a single file. The multicast router multicasts the message to the edge servers.",
            "target": ".demo_origin_server"
        }]
    
    # Create the Internet node
    data["default_setup"]["nodes"].append({
        "id": "0",
        "type": "custom",
        "data": {
            "id": "0",
            "name": "Internet",
            "ip": "0.0.0.0",
            "icon": "internet",
            "message": ""
        },
        "position": {
            "x": -400,
            "y": 150
        }
    })

    # Create the server node (one server only)
    data["default_setup"]["nodes"].append({
        "id": "server-1",
        "type": "custom",
        "data": {
            "id": "demo_origin_server",
            "name": "Main Server",
            "ip": "127.0.0.1",
            "icon": "server",
            "message": "Prepares the packet."
        },
        "position": {
            "x": -800,  # Moved to the left of the Internet node
            "y": 150
        }
    })

    # Create edge from server to Internet
    data["default_setup"]["edges"].append({
        "id": "server-internet",
        "source": "server-1",
        "target": "0",
        "animated": False,
        "style": {
            "strokeWidth": 3
        }
    })

    # Create multicast routers
    for i in range(1, nb_routers + 1):
        multicast_router_id = f"router-{i}"
        ip = f"224.0.0.{i}"
        data["routers"].append(ip)
        data["default_setup"]["nodes"].append({
            "id": multicast_router_id,
            "type": "custom",
            "data": {
                "id": multicast_router_id,
                "name": f"Multicast Router {i}",
                "ip": ip,
                "icon": "router",
                "message": ""
            },
            "position": {
                "x": -75,
                "y": 150 + (i - 1) * 200
            }
        })
        
        # Create edge from server to multicast router
        data["default_setup"]["edges"].append({
            "id": f"server-router-{i}",
            "source": "0",
            "target": multicast_router_id,
            "animated": False,
            "style": {
                "strokeWidth": 3
            }
        })

    # Create nodes for receivers
    for i in range(1, nb_receivers + 1):
        receiver_id = f"receiver-{i}"
        data["default_setup"]["nodes"].append({
            "id": receiver_id,
            "type": "custom",
            "data": {
                "id": receiver_id,
                "name": f"Receiver {i}",
                "ip": f"127.0.0.{i + 1}",
                "icon": "client",
                "message": "",
                "cache": [f"cache_{i}_1", f"cache_{i}_2"]
            },
            "position": {
                "x": 330,
                "y": 150 + (i - 1) * 200
            }
        })
        data["steps"].append({
                "target": f".{receiver_id}",
                "content": "The edge servers receive the same message and proceed with the decoding of the content using their respective cache.",
                "disableBeacon": True
            },)
        
        # Connect each multicast router to each receiver
        for j in range(1, nb_routers + 1):
            router_id = f"router-{j}"
            data["default_setup"]["edges"].append({
                "id": f"{router_id}-{receiver_id}",
                "source": router_id,
                "target": receiver_id,
                "animated": False,
                "style": {
                    "strokeWidth": 3
                }
            })

    data["steps"].append({
            "content": [
                "The edge servers requested 2 different files; each of them has a cache of 1 file size.\nThe origin server sent 50% of a file over the Internet.\nThe router multicast the message (50% of file size) to both edge servers\nThe edge servers can decode the entire file\nWithout cache-aided multicast, the origin server would have to send 100% of a file (at least)."
            ],
            "target": ".demo_origin_server"
        })
    data["steps"].append(
        {
            "content": [
                "vs. Traditional example (unicast; no coded caching)\nThe edge servers requested 2 different files\nEach of them has a cache of 1 file size\nBoth edge servers store at the cache the same file (i.e., the most popular)\nEdge server 1 has the requested file in the cache\nNo request from the origin server. Edge server 2 does not have the requested file and requests it from the origin server\nThe origin server sents the requested file (100% of a file size) to the edge server 2\n"
            ],
            "target": ".demo_origin_server"
        })
    # Write the updated data to a JSON file
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    
    return simulation_id


