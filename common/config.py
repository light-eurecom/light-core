import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SIMULATION_OUTPUT_PATH = os.getenv('OUTPUT_PATH', os.path.expanduser("~/var/light_eurecom/simulations"))
DATA_PATH = os.path.join(BASE_DIR, 'data')
VIDEO_PATH = os.path.join(DATA_PATH, "raw_videos")
UNICAST_PORT = 22211

if not os.path.exists(SIMULATION_OUTPUT_PATH):
    os.makedirs(SIMULATION_OUTPUT_PATH, exist_ok=True)
