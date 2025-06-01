#!/bin/bash

# Run the validator info service
echo "Starting Validator Info Service..."
echo "=================================="

/root/vasile/networksecuritybackend/fetch_metadata.sh

# Run the validator info service
python3 /root/vasile/networksecuritybackend/validator_info_service/main.py

echo "Validator Info Service completed!" 
