#!/bin/bash

echo "--- Step 1: Creating a virtual environment ---"
python3 -m venv .venv
if [ $? -ne 0 ]; then
    echo "Failed to create virtual environment."
    exit 1
fi
echo "Virtual environment created successfully."

echo "--- Step 2: Activating the virtual environment ---"
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment."
    exit 1
fi
echo "Virtual environment activated successfully."

echo "--- Step 3: Installing requirements ---"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to install requirements."
    exit 1
fi
echo "Requirements installed successfully."

echo "--- Step 4: Changing directory to redact and making migrations ---"
cd redact
if [ $? -ne 0 ]; then
    echo "Failed to change directory."
    exit 1
fi
python manage.py makemigrations
if [ $? -ne 0 ]; then
    echo "Failed to make migrations."
    exit 1
fi
echo "Migrations created successfully."

echo "--- Step 5: Installing Ollama ---"
pip install ollama
if [ $? -ne 0 ]; then
    echo "Failed to install Ollama."
    exit 1
fi
echo "Ollama installed successfully."