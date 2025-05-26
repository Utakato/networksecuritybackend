from datetime import datetime
from psycopg2.extras import execute_values

# SQL query constant for updating validators_data with IP addresses
UPDATE_VALIDATORS_IP_QUERY = """
    UPDATE validators_data 
    SET ip_address = data.ip_address, 
        last_ip_update = data.last_update
    FROM (VALUES %s) AS data(identity, ip_address, last_update)
    WHERE validators_data.identity_pubkey = data.identity
"""

# SQL query to add ip_address column if it doesn't exist
ADD_IP_ADDRESS_COLUMN = """
    ALTER TABLE validators_data 
    ADD COLUMN IF NOT EXISTS ip_address VARCHAR(50),
    ADD COLUMN IF NOT EXISTS last_ip_update TIMESTAMP
"""

def save_data_to_db(conn, data):
    """
    Update validators_data table with IP addresses based on identity matching
    """
    now = datetime.now()
    
    # First, ensure the ip_address column exists
    try:
        with conn.cursor() as cur:
            cur.execute(ADD_IP_ADDRESS_COLUMN)
            conn.commit()
    except Exception as e:
        print(f"Note: {e}")
        conn.rollback()
    
    # Prepare the data for batch update
    records = [
        (row['Identity'], row['IP Address'], now) 
        for row in data
    ]
    
    try:
        with conn.cursor() as cur:
            # Use batch update to match identity and update IP address
            execute_values(cur, UPDATE_VALIDATORS_IP_QUERY, records)
            
            rows_affected = cur.rowcount
            conn.commit()
            
            print(f"Updated {rows_affected} validator records with IP addresses")
    except Exception as e:
        conn.rollback()
        print(f"Error updating validators with IP addresses: {e}")
        raise
