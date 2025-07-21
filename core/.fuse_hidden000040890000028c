#!/bin/bash

# Define the virtual environment directory
VENV_DIR=".venv"

# Check if the virtual environment directory exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment."
        exit 1
    fi
fi

# Activate the virtual environment
source $VENV_DIR/bin/activate

# Install or update requirements
echo "Installing/updating requirements..."
pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
	echo "Failed to install requirements."
	deactivate
	exit 1
fi

# Run the FastAPI application using uvicorn
echo "Starting FastAPI server with uvicorn..."
uvicorn core_api:app --host 0.0.0.0 --port 9555 --reload

# Deactivate the virtual environment when the server is stopped
deactivate
echo "Server stopped. Virtual environment deactivated."
