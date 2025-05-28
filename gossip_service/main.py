#!/usr/bin/env python3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from parse_gossip_data import parse_gossip_data_for_db
from db_service.connection import get_db_connection
from save_gossip_to_db import save_data_to_db

# fetch_data.sh
def main():
    
    # Connect to the database
    try:
        conn = get_db_connection()
        
        # Parse data directly from JSON file
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        gossip_data_path = os.path.join(script_dir, 'gossip_data.json')
        gossip_data = parse_gossip_data_for_db(gossip_data_path)
        
        # Save the data to the database
        save_data_to_db(conn, gossip_data)
        
        # Close the connection
        conn.close()
        print("Database connection closed")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
