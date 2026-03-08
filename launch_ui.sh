#!/bin/bash
# SoftMech UI Launcher - Bash Script (for Linux/macOS)
# Simple launcher for the SoftMech Designer UI

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate the virtual environment if it exists
if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
else
    echo "Warning: Virtual environment not found at .venv"
    echo "Please ensure you have activated the correct Python environment"
fi

# Launch the UI
echo "Launching SoftMech Designer UI..."
python "$SCRIPT_DIR/softmech_cli.py" ui
