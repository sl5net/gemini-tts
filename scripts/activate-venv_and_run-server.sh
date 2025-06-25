#!/bin/bash

# This script navigates to the project directory,
# activates the virtual environment, and then starts the Python server.
# Using 'exec' replaces the shell process with the python process.

# Get the directory where this script is located
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# Go one level up to the project root
PROJECT_DIR=$(dirname "$SCRIPT_DIR")

cd "$PROJECT_DIR"
source "$PROJECT_DIR/venv/bin/activate"
exec python "$PROJECT_DIR/speak_server.py"
