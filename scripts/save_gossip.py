#!/usr/bin/env python3

import dotenv
from csv_module.read_csv import read_csv_data
from db_module.connection import get_db_connection
from db_module.create_table import create_table_if_not_exists
from db_module.save_gossip_to_db import save_data_to_db

# Try to load .env file if it exists
try:
    dotenv.load_dotenv()
except:
    print("No .env file found, using default connection parameters")



def main():

    # fetch_data.sh

    # Parse data from json to DF
    # DF to CSV
    # CSV to DB
    
    # Connect to the database
    try:
        conn = get_db_connection()
        
        # Create the table if it doesn't exist
        create_table_if_not_exists(conn)
        
        # Read data from the CSV file
        data = read_csv_data('gossip_extracted_simple.csv')
        
        # Save the data to the database
        save_data_to_db(conn, data)
        
        # Close the connection
        conn.close()
        print("Database connection closed")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
