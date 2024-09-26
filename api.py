import json
import os
import threading
import time
from gevent.pywsgi import WSGIServer
from flask import Flask, jsonify, request
import subprocess
from flask_cors import CORS
from werkzeug.exceptions import BadRequest
from common.utils import create_simulation_schema
from package.logger_manager import LoggerManager
from dotenv import load_dotenv
from common.config import SIMULATION_OUTPUT_PATH

load_dotenv('.env.development')
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

print("Allowed origins:", os.getenv('LIGHT_HOST'))

# Configure CORS for all routes
CORS(app)


# Dictionary to track running simulation processes
simulation_processes = {}

def is_valid_command(commands):
    """Ensure the commands are valid before running them."""
    
    # Check for specific command structure
    if commands[:2] in [["python3", "receiver.py"], ["python3", "server.py"]]:
        try:
            # Validate argument structure for receiver
            if commands[1] == "receiver.py":
                rq_value = int(commands[3])
                if rq_value < 1 or rq_value > 5:
                    return False

                int_arg = int(commands[2])
                if int_arg < 1 or int_arg > 5:
                    return False
                
                return commands[4:] == ["-c", "receiver.ini"]

            # Validate argument structure for server
            elif commands[1] == "server.py":
                int_arg = int(commands[2])
                if int_arg < 1 or int_arg > 5:
                    return False
                
                return commands[3:] == ["-c", "server.ini"]

        except (ValueError, IndexError):
            # Catching index errors for missing arguments or value errors for non-integer inputs
            return False
    
    return False

def read_stream(stream, stream_name, sim_id, on_error=False):
    """Helper function to read the stream and print it in real-time."""
    logger = LoggerManager(sim_id)
    while True:
        output = stream.readline()
        if output:
            print(str(f"{output.strip()}"))
            logger.update("logs", str(f"{output.strip()}"), append=True)
            if str(output.strip()).startswith("ERROR") or str(output.strip()).startswith("CRITICAL") or on_error: 
                logger.update("status", "error")
            elif str(output.strip()).startswith("FINISHED"):
                logger.update("status", "complete")

        if output == '' and stream.closed:
            break

def start_process(commands, sim_id):
    """Start the process and read the output in a non-blocking way."""
    # Start the process
    print(f'Running command: {" ".join(commands)}')
    process = subprocess.Popen(
        commands,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Create separate threads to read stdout and stderr in real-time
    stdout_thread = threading.Thread(target=read_stream, args=(process.stdout, "STDOUT", sim_id))
    stderr_thread = threading.Thread(target=read_stream, args=(process.stderr, "STDERR", sim_id, True))  # Set on_error to True for stderr

    # Start the threads
    stdout_thread.start()
    stderr_thread.start()

    # Wait for the process to finish
    process.wait()

    # Wait for the threads to finish
    stdout_thread.join()
    stderr_thread.join()

    print(f"Process finished with exit code {process.returncode}")
    
def start_process_in_background(commands, sim_id):
    """Start the process in the background."""
    thread = threading.Thread(target=start_process, args=(commands, sim_id))
    thread.start()
    
@app.route('/create_simulation', methods=['POST'])
def create_simulation():
    """Create a simulation and start the process without streaming events."""
    data = request.json
    try:
        nb_receivers = int(data.get('nb_receivers', 1))
        nb_routers = int(data.get('nb_routers', 1))
        if nb_receivers <= 0 or nb_routers <= 0:
            raise BadRequest("Number of receivers and routers must be greater than 0.")
    except (ValueError, TypeError) as e:
        return jsonify({"error": "Invalid input"}), 400

    # Simulate creating a unique simulation ID
    simulation_id = create_simulation_schema(nb_receivers, nb_routers)

    # Commands to start server and client
    commands_server = ["python3", "server.py", "2", "-c", "server.ini", "-sim_id", simulation_id]
    commands_client = ["python3", "receiver.py", "1", "-rq", "2", "-c", "receiver.ini", "-sim_id", simulation_id]
    commands_client2 = ["python3", "receiver.py", "2", "-rq", "5", "-c", "receiver.ini", "-sim_id", simulation_id]

    # Start the server and client processes in the background
    start_process_in_background(commands_server, simulation_id)
    time.sleep(2)
    start_process_in_background(commands_client, simulation_id)
    time.sleep(1)
    start_process_in_background(commands_client2, simulation_id)


    return jsonify({"simulation_id": simulation_id}), 201

@app.route('/simulations/<simulation_id>')
def get_simulation(simulation_id):
    try:
        simulation_path = os.path.join(SIMULATION_OUTPUT_PATH, f'{simulation_id}.json')
        with open(simulation_path, 'r') as file:
            simulation = json.load(file)
        return jsonify(simulation), 200
    except FileNotFoundError:
        return jsonify({'error': 404}), 404

@app.route('/simulations')
def get_simulations():
    try:
        simulations = []
        
        for filename in os.listdir(SIMULATION_OUTPUT_PATH):
            if filename.endswith(".json"):
                with open(os.path.join(SIMULATION_OUTPUT_PATH, filename), 'r') as file:
                    simulation_data = json.load(file)
                    simulations.append({"id":simulation_data["id"], "status":simulation_data["status"] })
        
        return jsonify(simulations), 200
    except FileNotFoundError:
        return jsonify([]), 404
    
@app.route('/health', methods=['GET'])
def ping():
    return jsonify({'message': 'Server is running', "status":"ok"}), 200

if __name__ == '__main__':
    http_server = WSGIServer(('', 5002), app)
    http_server.serve_forever()
