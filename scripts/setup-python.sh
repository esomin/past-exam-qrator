#!/bin/bash
# Setup Python virtual environment and install dependencies

cd python

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Python setup complete!"
echo "To activate the virtual environment, run: source python/.venv/bin/activate"
echo "To start the Flask server, run: python python/app.py"