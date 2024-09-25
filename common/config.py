import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SIMULATION_OUTPUT_PATH = os.getenv('OUTPUT_PATH', os.path.expanduser("~/var/light_eurecom/simulations"))
CACHE_PATH = os.getenv('OUTPUT_PATH', os.path.expanduser("~/var/tmp/light_eurecom/cache"))
DATA_PATH = os.path.join(BASE_DIR, 'data')
VIDEO_PATH = os.path.join(DATA_PATH, "raw_videos")
UNICAST_PORT = 3224

if not os.path.exists(SIMULATION_OUTPUT_PATH):
    os.makedirs(SIMULATION_OUTPUT_PATH, exist_ok=True)

if not os.path.exists(CACHE_PATH):
    os.makedirs(CACHE_PATH, exist_ok=True)