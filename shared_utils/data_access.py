#!/usr/bin/env python3

import sys
import os

# Add the parent directory to the path to import db_module
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from db_service.connection import get_db_connection


GET_ALL_IP_ADDRESSES_QUERY = """
    SELECT DISTINCT ON (g.identity_key)
        g.identity_key,
        g.ip_address
    FROM gossip_peers g
    JOIN (
        SELECT vs1.identity_key, vs1.activated_stake
        FROM validators_state vs1
        INNER JOIN (
            SELECT identity_key, MAX(timestamp) AS max_timestamp
            FROM validators_state
            GROUP BY identity_key
        ) vs2 ON vs1.identity_key = vs2.identity_key AND vs1.timestamp = vs2.max_timestamp
    ) v ON g.identity_key = v.identity_key
    WHERE g.ip_address IS NOT NULL
      AND g.identity_key IS NOT NULL
      AND v.activated_stake >= 10000 * 1e9
    ORDER BY g.identity_key, g.timestamp DESC
"""

def get_all_ip_addresses():
    """
    Get all unique IP addresses and their corresponding identity keys from gossip_peers table
    Based on unique identity keys - each validator identity is tracked separately
    
    Returns:
        list: List of dictionaries containing ip_address and identity_key
    """
    conn = None
    try:
        # Connect to the database (show connection info once)
        print("📡 Connecting to database to retrieve IP addresses...")
        conn = get_db_connection(verbose=True)
        
        with conn.cursor() as cur:
            # Get the most recent entry for each identity_key
            # This ensures each validator identity is tracked separately
 
            cur.execute(GET_ALL_IP_ADDRESSES_QUERY)
            results = cur.fetchall()
            
            # Convert to list of dictionaries
            ip_data = []
            for row in results:
                ip_data.append({
                    'identity_key': row[0],
                    'ip_address': row[1]
                })
            
            print(f"Retrieved {len(ip_data)} unique identity keys with IP addresses from gossip_peers table")
            return ip_data
            
    except Exception as e:
        print(f"Error retrieving IP addresses from database: {e}")
        return []
    finally:
        if conn:
            conn.close()

def main():
    """
    Main function for testing the get_all_ip_addresses function
    """
    ip_data = get_all_ip_addresses()
    
    if ip_data:
        print("\nSample IP addresses and identity keys:")
        for i, data in enumerate(ip_data[:5]):  # Show first 5 entries
            print(f"{i+1}. IP: {data['ip_address']}, Identity: {data['identity_key']}")
        
        if len(ip_data) > 5:
            print(f"... and {len(ip_data) - 5} more entries")
    else:
        print("No IP addresses found")

if __name__ == "__main__":
    main() 