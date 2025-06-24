# speak_file.py
import argparse
import subprocess
import requests
import time
import os
import sys

# --- Find project root from this script's location ---
SCRIPT_PATH = os.path.realpath(__file__)
PROJECT_ROOT = os.path.dirname(SCRIPT_PATH)
START_SERVER_SCRIPT = os.path.join(PROJECT_ROOT, 'scripts', 'activate-venv_and_run-server.sh')
# ---

# --- Server Configuration ---
HOST = '127.0.0.1'
PORT = 5002
HTTPS_URL = f"https://{HOST}:{PORT}/speak"
HTTP_URL = f"http://{HOST}:{PORT}/speak"
# ---

parser = argparse.ArgumentParser(description="Helper-Script for the Dictation-Service")
parser.add_argument('file', help='Text file to be read')
args = parser.parse_args()

with open(args.file, 'r') as f:
    content = f.read()

with open('/tmp/speak_server_input.txt', 'w') as f:
    f.write(content)

service_name = "speak_server.py"
check_command = ['pgrep', '-f', service_name]

# Check if server is running
result = subprocess.run(check_command, capture_output=True)
url_to_use = HTTPS_URL # Standardmäßig HTTPS versuchen

if result.returncode != 0:
    print(f"'{service_name}' not running. Starting it now...")
    subprocess.Popen([START_SERVER_SCRIPT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("Waiting for server to become ready...")
    server_ready = False
    max_wait_time = 10
    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        try:
            # Zuerst HTTPS versuchen
            requests.head(HTTPS_URL, verify=False, timeout=1)
            print("Server is ready on HTTPS!")
            url_to_use = HTTPS_URL
            server_ready = True
            break
        except requests.exceptions.SSLError:
            # Wenn SSL fehlschlägt, ist der Server wahrscheinlich im HTTP-Modus
            print("SSL failed, trying HTTP...")
            try:
                requests.head(HTTP_URL, timeout=1)
                print("Server is ready on HTTP!")
                url_to_use = HTTP_URL
                server_ready = True
                break
            except requests.exceptions.ConnectionError:
                time.sleep(0.5) # Server vielleicht noch nicht ganz oben
        except requests.exceptions.ConnectionError:
            time.sleep(0.5)

    if not server_ready:
        log_path = os.path.join(PROJECT_ROOT, 'server.log')
        print(f"Server did not start within {max_wait_time} seconds.")
        print(f"Please check the log file for errors: '{log_path}'")
        sys.exit(1)

# Jetzt wissen wir, welche URL wir benutzen müssen (url_to_use)
print(f"Sending request to server at {url_to_use}...")
try:
    # Verwende die URL, die im Health-Check funktioniert hat
    response = requests.post(url_to_use, verify=False)
    print(f"Server response: {response.status_code}")
except Exception as e:
    print(f"Failed to connect to the server: {e}")
