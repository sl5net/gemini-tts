import subprocess
import time
from pathlib import Path
import os
import requests


content = clipboard.get_clipboard()
with open('/tmp/speak_server_input.txt', 'w') as f:
    f.write(content)
time.sleep(0.2)

# --- Server Configuration ---
HOST = '127.0.0.1'
PORT = 5002
HTTPS_URL = f"https://{HOST}:{PORT}/speak"
HTTP_URL = f"http://{HOST}:{PORT}/speak"
# ---

try:
    requests.head(HTTPS_URL, verify=False, timeout=1)
    url_to_use = HTTPS_URL
except requests.exceptions.RequestException:
    requests.head(HTTP_URL, timeout=1)
    url_to_use = HTTP_URL

response = requests.post(url_to_use, verify=False)

