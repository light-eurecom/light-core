import ast
from collections import defaultdict

class Cache:
    def __init__(self, filename='cache.txt'):
        self.filename = filename

    def get_content(self):
        try:
            with open(self.filename, 'r') as file:
                content = file.read()
                dict_data = ast.literal_eval(content)
                default_dict_data = defaultdict(dict)
                for (key1, key2), value in dict_data.items():
                    default_dict_data[key1][key2] = value
                return default_dict_data
        except FileNotFoundError:
            return ""

    def set_content(self, content):
        with open(self.filename, 'w') as file:
            file.write(content)
