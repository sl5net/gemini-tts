#!/bin/bash
# this is scripts/activate-venv_and_run-server.sh

# Exit immediately if a command fails
set -e

# This line is the key: It finds the absolute path of the directory
# where the script itself is located (i.e., the 'scripts' directory).
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo "SCRIPT_DIR: $SCRIPT_DIR"

# The project's root directory is one level above the script's directory.
PROJECT_ROOT="$SCRIPT_DIR/.."
echo "PROJECT_ROOT: $PROJECT_ROOT"

echo "Activating virtual environment at '$PROJECT_ROOT/venv'..."
source "$PROJECT_ROOT/venv/bin/activate"
echo  "$PROJECT_ROOT/venv/bin/activate"

echo "Starting Python server from '$PROJECT_ROOT'..."
# We run the python script using its absolute path to be safe
# python3 "$PROJECT_ROOT/speak_server.py"

# keep server running even after you close the terminal:

python3 "$PROJECT_ROOT/speak_server.py" # # node when we maybe want use, but i like close the server by closing terminal nohup > "$PROJECT_ROOT/server.log" 2>&1 &

