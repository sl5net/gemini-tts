import argparse
import tempfile
import requests

parser = argparse.ArgumentParser(description="Helper-Script für den Dictation-Service")
parser.add_argument('file', help='Textdatei, die gelesen werden soll')
args = parser.parse_args()

with open(args.file, 'r') as f:
    content = f.read()

with open('/tmp/speak_server_input.txt', 'w') as f:
    f.write(content)

url = "https://127.0.0.1:5002/speak"
response = requests.post(url, verify=False)


