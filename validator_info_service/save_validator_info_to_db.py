#!/usr/bin/env python3
"""
Script to save validator information data from JSON to TimescaleDB database
"""

import sys
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from psycopg2.extras import execute_values
import psycopg2

# Add the parent directory to the path to import db_module
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from db_service.connection import get_db_connection

# SQL Queries
CREATE_VALIDATOR_INFO_TABLE = """
    CREATE TABLE IF NOT EXISTS validator_info (
        identity_pubkey TEXT NOT NULL,
        info_pubkey TEXT,
        name TEXT,
        details TEXT,
        website TEXT,
        icon_url TEXT,
        keybase_username TEXT,
        timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY (identity_pubkey, timestamp)
    );
    
    -- Create hypertable for TimescaleDB if not already created
    SELECT create_hypertable('validator_info', 'timestamp', if_not_exists => TRUE);
"""

# SQL query for inserting validator info data into TimescaleDB
INSERT_VALIDATOR_INFO_QUERY = """
    INSERT INTO validator_info (
        identity_pubkey, info_pubkey, name, details, website, 
        icon_url, keybase_username, timestamp
    )
    VALUES %s
    ON CONFLICT (identity_pubkey, timestamp) DO UPDATE SET
        info_pubkey = EXCLUDED.info_pubkey,
        name = EXCLUDED.name,
        details = EXCLUDED.details,
        website = EXCLUDED.website,
        icon_url = EXCLUDED.icon_url,
        keybase_username = EXCLUDED.keybase_username
"""

def create_validator_info_table(conn):
    """
    Create the validator_info table if it doesn't exist and set up TimescaleDB hypertable
    
    Args:
        conn: Database connection object
    """
    with conn.cursor() as cur:
        try:
            print("Creating validator_info table and hypertable...")
            cur.execute(CREATE_VALIDATOR_INFO_TABLE)
            print("Table 'validator_info' and hypertable created successfully")
            conn.commit()
        except Exception as e:
            print(f"Note: Table creation/hypertable setup: {e}")
            conn.rollback()

def load_validator_info_json(file_path: str) -> List[Dict[str, Any]]:
    """
    Load validator information data from JSON file
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        List of validator info dictionaries
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        print(f"Loaded {len(data)} validator info records from {file_path}")
        return data
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {e}")
        return []
    except Exception as e:
        print(f"Error loading file: {e}")
        return []

def save_validator_info_to_db(validator_info_data: List[Dict[str, Any]], conn, batch_size: int = 1000):
    """
    Save validator info data to the TimescaleDB validator_info table
    
    Args:
        validator_info_data: List of validator info dictionaries
        conn: Database connection
        batch_size: Number of records to insert per batch
    """
    if not validator_info_data:
        print("No validator info data to save")
        return 0
    
    # Use current timestamp for this batch
    now = datetime.now()
    snapshot_timestamp = now.replace(second=0, microsecond=0)
    
    # Deduplicate by identity_pubkey - keep the most complete record for each validator
    print("Deduplicating validator records...")
    validators_by_pubkey = {}
    
    for validator in validator_info_data:
        identity_pubkey = validator.get('identityPubkey')
        if not identity_pubkey:
            continue
            
        # If we haven't seen this pubkey before, or if this record has more info, keep it
        if identity_pubkey not in validators_by_pubkey:
            validators_by_pubkey[identity_pubkey] = validator
        else:
            # Compare completeness - prefer record with more non-empty fields
            existing = validators_by_pubkey[identity_pubkey]
            existing_info = existing.get('info', {})
            current_info = validator.get('info', {})
            
            # Count non-empty fields in each record
            existing_fields = sum(1 for v in existing_info.values() if v and str(v).strip())
            current_fields = sum(1 for v in current_info.values() if v and str(v).strip())
            
            # Keep the record with more information
            if current_fields > existing_fields:
                validators_by_pubkey[identity_pubkey] = validator
    
    print(f"Deduplicated from {len(validator_info_data)} to {len(validators_by_pubkey)} unique validators")
    
    # Prepare records for batch insert
    records = []
    for identity_pubkey, validator in validators_by_pubkey.items():
        info_pubkey = validator.get('infoPubkey')
        
        # Extract info fields
        info = validator.get('info', {})
        name = info.get('name', '')
        details = info.get('details', '')
        website = info.get('website', '')
        icon_url = info.get('iconUrl', '')
        keybase_username = info.get('keybaseUsername', '')
        
        records.append((
            identity_pubkey,
            info_pubkey,
            name,
            details,
            website,
            icon_url,
            keybase_username,
            snapshot_timestamp
        ))
    
    if not records:
        print("No valid records to insert")
        return 0
    
    print(f"Preparing to save {len(records)} unique validator info records to database...")
    
    # Insert data in batches using execute_values for efficiency
    total_inserted = 0
    
    try:
        with conn.cursor() as cur:
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                
                execute_values(cur, INSERT_VALIDATOR_INFO_QUERY, batch)
                batch_inserted = len(batch)
                total_inserted += batch_inserted
                print(f"Inserted batch {i//batch_size + 1}: {batch_inserted} records")
        
        conn.commit()
        print(f"Successfully saved {total_inserted} validator info records to database for {snapshot_timestamp}")
        return total_inserted
        
    except Exception as e:
        print(f"Error inserting validator info data: {e}")
        conn.rollback()
        raise

def get_validator_info_stats(conn):
    """
    Get statistics about the validator_info table
    
    Args:
        conn: Database connection
    """
    try:
        with conn.cursor() as cur:
            # Get total count
            cur.execute("SELECT COUNT(*) FROM validator_info")
            total_count = cur.fetchone()[0]
            
            # Get unique validators count
            cur.execute("SELECT COUNT(DISTINCT identity_pubkey) FROM validator_info")
            unique_validators = cur.fetchone()[0]
            
            # Get latest timestamp
            cur.execute("SELECT MAX(timestamp) FROM validator_info")
            latest_timestamp = cur.fetchone()[0]
            
            # Get validators with names
            cur.execute("SELECT COUNT(DISTINCT identity_pubkey) FROM validator_info WHERE name IS NOT NULL AND name != ''")
            validators_with_names = cur.fetchone()[0]
            
            # Get validators with websites
            cur.execute("SELECT COUNT(DISTINCT identity_pubkey) FROM validator_info WHERE website IS NOT NULL AND website != ''")
            validators_with_websites = cur.fetchone()[0]
            
            print(f"\n{'='*50}")
            print("VALIDATOR INFO TABLE STATISTICS")
            print(f"{'='*50}")
            print(f"Total records: {total_count:,}")
            print(f"Unique validators: {unique_validators:,}")
            print(f"Latest data timestamp: {latest_timestamp}")
            print(f"Validators with names: {validators_with_names:,}")
            print(f"Validators with websites: {validators_with_websites:,}")
            print(f"{'='*50}")
            
    except Exception as e:
        print(f"Error getting statistics: {e}")

def main(file_path: Optional[str] = None):
    """
    Main function to load validator info data and save to database
    
    Args:
        file_path: Optional path to validator info JSON file
    """
    if file_path is None:
        file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'validator_info.json')
    
    try:
        # Load validator info data
        print("Loading validator info data...")
        validator_info_data = load_validator_info_json(file_path)
        
        if not validator_info_data:
            print("No data to save")
            return
            
        # Connect to database
        print("Connecting to database...")
        conn = get_db_connection()
        
        # Create table if needed
        create_validator_info_table(conn)
        
        # Save data
        print("Saving validator info data...")
        records_saved = save_validator_info_to_db(validator_info_data, conn)
        
        # Show statistics
        get_validator_info_stats(conn)
        
        # Close connection
        conn.close()
        
        print(f"\n{'='*50}")
        print(f"VALIDATOR INFO IMPORT COMPLETED")
        print(f"Records saved: {records_saved:,}")
        print(f"{'='*50}")
        
    except Exception as e:
        print(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Save validator info data to TimescaleDB')
    parser.add_argument('--file', type=str, help='Path to validator info JSON file')
    
    args = parser.parse_args()
    main(args.file) 