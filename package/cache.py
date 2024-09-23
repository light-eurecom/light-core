import ast
from collections import defaultdict
from common.utils import custom_logger
class Cache:
    def __init__(self, filename='cache.txt'):
        self.filename = filename

    def get_content(self):
        try:
            with open(self.filename, 'r') as file:
                content = file.read().strip()
                if content:
                    dict_data = ast.literal_eval(content)
                    if isinstance(dict_data, dict):
                        default_dict_data = defaultdict(dict)
                        for key1, inner_dict in dict_data.items():
                            for key2, value in inner_dict.items():
                                default_dict_data[key1][key2] = value
                        return default_dict_data
                    else:
                        custom_logger(f"Error: {self.filename} does not contain a valid dictionary.", level="error")
                        return defaultdict(dict)
                else:
                    custom_logger(f"Error reading {self.filename}: {e}", level="error")
                    return defaultdict(dict)
        except FileNotFoundError:
            custom_logger(f"Error: {self.filename} not found.", level="error")
            return defaultdict(dict)
        except Exception as e:
            custom_logger(f"Error reading {self.filename}: {e}", level="error")
            return defaultdict(dict)

    def set_content(self, content):
        try:
            with open(self.filename, 'w') as file:
                file.write(str(content))
        except Exception as e:
            print(f"Error writing to {self.filename}: {e}")
