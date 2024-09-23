import json
import os
from typing import Union, List
from common.config import SIMULATION_OUTPUT_PATH
class LoggerManager:
    def __init__(self, sim_id: str):
        self.sim_id = sim_id
        self.file_path = os.path.join(SIMULATION_OUTPUT_PATH, f"{sim_id}.json")
        self._ensure_file_exists()  # Ensure file is created if it doesn't exist
        self.data = self._load_json()

    def _ensure_file_exists(self):
        """Ensure that the JSON file exists. If it doesn't, create an empty one."""
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)  # Create folder if it doesn't exist
            with open(self.file_path, "w") as f:
                json.dump({}, f, indent=4)  # Create an empty JSON file
            print(f"File created at {self.file_path}")

    def _load_json(self) -> dict:
        """Load the JSON data from the file, or initialize an empty dict if the file does not exist."""
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            raise ValueError(f"Error decoding JSON from file {self.file_path}")

    def _save_json(self):
        """Save the current data to the JSON file."""
        with open(self.file_path, "w") as f:
            json.dump(self.data, f, indent=4)

    def update(self, keys: Union[str, List[str]], new_value, append=False):
        """Update the JSON data with the given keys and new value.
        
        Args:
            keys (Union[str, List[str]]): A key or list of keys specifying the path to the value.
            new_value: The new value to set.
            append (bool): If True, append the new value to the existing array if the target is an array.
        """
        if isinstance(keys, str):
            keys = keys.split("][")

        data = self.data
        
        # Navigate through the keys to the final level
        for key in keys[:-1]:
            if key not in data or not isinstance(data[key], dict):
                data[key] = {}
            data = data[key]

        # Check if the final key points to an array
        final_key = keys[-1]
        if append:
            # If the final key exists and is an array, append the new value
            if final_key in data and isinstance(data[final_key], list):
                data[final_key].append(str(new_value))
            else:
                # If the key doesn't exist or isn't a list, initialize it as a list
                data[final_key] = [str(new_value)]
        else:
            # Otherwise, just set the new value normally
            data[final_key] = str(new_value)

        # Save the updated JSON
        self._save_json()

