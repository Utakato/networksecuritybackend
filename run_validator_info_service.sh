#!/bin/bash

# Run the validator info service
echo "Starting Validator Info Service..."
echo "=================================="

/root/vasile/networksecuritybackend/fetch_metadata.sh

# Check if the data file exists
if [ ! -f "data/validator_info.json" ]; then
    echo "Error: data/validator_info.json file not found!"
    echo "Please ensure the validator info data file exists."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
else
    # Activate virtual environment
    source venv/bin/activate
fi

# Run the validator info service
python3 validator_info_service/main.py

echo "Validator Info Service completed!" 
