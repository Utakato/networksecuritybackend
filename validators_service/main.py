
import os
import sys

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# import modules
from validators_service.save_validators_to_db import main as save_to_db

def main():

    # get the path to the validatorsa data file
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'validators_data.json')
    
    # save the validators data to the database
    try:
        save_to_db(file_path)
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 