#!/usr/bin/env python3
"""
Script to save validators data from DataFrame to TimescaleDB database
"""

import sys
import os
import pandas as pd
from datetime import datetime
from typing import Optional
from psycopg2.extras import execute_values

# Add the parent directory to the path to import db_module
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from db_service.connection import get_db_connection
from validators_service.parse_validators_data import load_validators_json, parse_validators_to_dataframe

# SQL Queries
CREATE_VALIDATORS_STATE_TABLE = """
    CREATE TABLE IF NOT EXISTS validators_state (
        identity_key TEXT NOT NULL,
        vote_account TEXT,
        commission INTEGER,
        version TEXT,
        is_delinquent BOOLEAN,
        skip_rate NUMERIC,
        activated_stake BIGINT,
        credits BIGINT,
        last_vote BIGINT,
        root_slot BIGINT,
        epoch_credits BIGINT,
        timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY (identity_key, timestamp)
    );
    
    -- Create hypertable for TimescaleDB if not already created
    SELECT create_hypertable('validators_state', 'timestamp', if_not_exists => TRUE);
"""

# SQL query for inserting validator state data into TimescaleDB
INSERT_VALIDATORS_STATE_QUERY = """
    INSERT INTO validators_state (
        identity_key, vote_account, commission, version, is_delinquent,
        skip_rate, activated_stake, credits, last_vote, root_slot,
        epoch_credits, timestamp
    )
    VALUES %s
    ON CONFLICT (identity_key, timestamp) DO UPDATE SET
        vote_account = EXCLUDED.vote_account,
        commission = EXCLUDED.commission,
        version = EXCLUDED.version,
        is_delinquent = EXCLUDED.is_delinquent,
        skip_rate = EXCLUDED.skip_rate,
        activated_stake = EXCLUDED.activated_stake,
        credits = EXCLUDED.credits,
        last_vote = EXCLUDED.last_vote,
        root_slot = EXCLUDED.root_slot,
        epoch_credits = EXCLUDED.epoch_credits
"""

def create_validators_tables(conn):
    """
    Create the validators_state table if it doesn't exist and set up TimescaleDB hypertable
    
    Args:
        conn: Database connection object
    """
    with conn.cursor() as cur:
        try:
            print("Creating validators_state table and hypertable...")
            cur.execute(CREATE_VALIDATORS_STATE_TABLE)
            print("Table 'validators_state' and hypertable created successfully")
            conn.commit()
        except Exception as e:
            print(f"Note: Table creation/hypertable setup: {e}")
            conn.rollback()

def save_validators_dataframe_to_db(df: pd.DataFrame, conn, batch_size: int = 1000):
    """
    Save validators DataFrame to the TimescaleDB validators_state table
    
    Args:
        df: Validators DataFrame
        conn: Database connection
        batch_size: Number of records to insert per batch
    """
    if df.empty:
        print("No validators data to save")
        return 0
    
    # Use current date at midnight for consistent daily snapshots
    now = datetime.now()
    snapshot_timestamp = now.replace(second=0, microsecond=0)
    
    # Prepare the data for insertion
    df_copy = df.copy()
    


    # Prepare records for batch insert
    records = []
    for _, row in df_copy.iterrows():
        # Extract fields with flexible naming
        identity_key = row.get('identityPubkey') or row.get('identity_key')
        vote_account = row.get('voteAccountPubkey') or row.get('vote_account')
        commission = row.get('commission')
        version = row.get('version')
        is_delinquent = row.get('delinquent') or row.get('is_delinquent')
        skip_rate = row.get('skipRate') or row.get('skip_rate')
        activated_stake = row.get('activatedStake') or row.get('activated_stake')
        credits = row.get('credits')
        last_vote = row.get('lastVote') or row.get('last_vote')
        root_slot = row.get('rootSlot') or row.get('root_slot')
        epoch_credits = row.get('epochCredits') or row.get('epoch_credits')
        
        # Skip records without required fields
        if not identity_key:
            continue
            
        records.append((
            identity_key,
            vote_account,
            commission,
            version,
            is_delinquent,
            skip_rate,
            activated_stake,
            credits,
            last_vote,
            root_slot,
            epoch_credits,
            snapshot_timestamp
        ))
    
    if not records:
        print("No valid records to insert")
        return 0
    
    print(f"Preparing to save {len(records)} validators to database...")
    
    # Insert data in batches using execute_values for efficiency
    total_inserted = 0
    
    try:
        with conn.cursor() as cur:
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                
                execute_values(cur, INSERT_VALIDATORS_STATE_QUERY, batch)
                batch_inserted = len(batch)
                total_inserted += batch_inserted
                print(f"Inserted batch {i//batch_size + 1}: {batch_inserted} records")
        
        conn.commit()
        print(f"Successfully saved {total_inserted} validators to database for {snapshot_timestamp.date()}")
        return total_inserted
        
    except Exception as e:
        print(f"Error inserting validators data: {e}")
        conn.rollback()
        raise

def main(file_path: Optional[str] = None):
    """
    Main function to load data and save to database
    
    Args:
        file_path: Optional path to validators JSON file
    """
    if file_path is None:
        file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'validators_data.json')
    
    try:
        # Load and parse data
        print("Loading validators data...")
        validators_data = load_validators_json(file_path)
        
        print("Parsing to DataFrame...")
        df = parse_validators_to_dataframe(validators_data)
        
        if df.empty:
            print("No data to save")
            return
            
        # Connect to database
        print("Connecting to database...")
        conn = get_db_connection()
        
        # Create tables if needed
        create_validators_tables(conn)
        
        # Save data
        print("Saving validators data...")
        validators_saved = save_validators_dataframe_to_db(df, conn)
        
        # Close connection
        conn.close()
        
        print(f"\n{'='*50}")
        print("DATABASE SAVE COMPLETE")
        print(f"{'='*50}")
        print(f"Validators saved: {validators_saved}")
        print(f"Collection timestamp: {datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).date()}")
        
    except Exception as e:
        print(f"Error saving to database: {e}")
        raise

if __name__ == "__main__":
    import sys
    
    # Allow file path as command line argument
    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    main(file_path) 