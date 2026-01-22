#!/bin/bash
set -e

# Create virtualenv if missing
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

# Activate venv for this shell
source venv/bin/activate

# Install requirements
python3 -m pip install -r requirements.txt

# Change into src and run main.py in a detached tmux session
cd src
python3 main.py