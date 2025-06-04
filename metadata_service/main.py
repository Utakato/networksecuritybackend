#!/usr/bin/env python3
"""
Main entry point for the validator info service
"""

import sys
import os

# Add the current directory to path
sys.path.append(os.path.dirname(__file__))

from metadata_service.save_metadata_to_db import main

if __name__ == "__main__":
    try:
        print("Starting validator info service...")
        main()
        print("Validator info service completed successfully!")
    except Exception as e:
        print(f"Error running validator info service: {e}")
        sys.exit(1) 