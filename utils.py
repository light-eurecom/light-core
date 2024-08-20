import base64
import configparser
import json
import os
from loguru import logger # type: ignore
import gzip
import io
import ast

logger.remove()  # Remove the default configuration (file handler)
logger.add(lambda msg: print(msg, end=''), colorize=True, format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>", level="INFO", diagnose=False)


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
    
    
def split_values(data, n):
    # Ensure the number n is smaller than the length of any "value"
    for file in data:
        if n > len(file['value']):
            raise ValueError(f"The provided number {n} is greater than the length of value '{file['value']}'")

    # Function to split a string into n equal parts
    def split_string_into_parts(value, n):
        k, m = divmod(len(value), n)
        return [value[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]

    result = []
    
    # Splitting each value into n parts
    for i in range(n):
        chunk = []
        for file in data:
            parts = split_string_into_parts(file['value'], n)
            chunk.append({
                "id": file['id'],
                "value": str(parts[i])
            })
        result.append(chunk)
    
    return result