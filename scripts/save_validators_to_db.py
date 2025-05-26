#!/usr/bin/env python3
"""
Script to save validators data from DataFrame to PostgreSQL database
"""

import sys
import os
import pandas as pd
from datetime import datetime
from typing import Optional

# Add the parent directory to the path to import db_module
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from db_module.connection import get_db_connection
from scripts.parse_validators_data import load_validators_json, parse_validators_to_dataframe, add_network_summary_info

# SQL Queries
CHECK_VALIDATORS_TABLE_EXISTS = """
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'validators_data'
);
"""

CREATE_VALIDATORS_TABLE = """
CREATE TABLE validators_data (
    id SERIAL PRIMARY KEY,
    identity_pubkey VARCHAR(100) NOT NULL,
    vote_account_pubkey VARCHAR(100) NOT NULL,
    commission INTEGER NOT NULL,
    last_vote BIGINT,
    root_slot BIGINT,
    credits BIGINT,
    epoch_credits INTEGER,
    activated_stake BIGINT NOT NULL,
    stake_in_sol DECIMAL(20, 9),
    version VARCHAR(20),
    delinquent BOOLEAN NOT NULL DEFAULT FALSE,
    skip_rate DECIMAL(10, 6),
    is_high_commission BOOLEAN DEFAULT FALSE,
    performance_score DECIMAL(10, 6),
    collected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(identity_pubkey, collected_at)
);
"""

CREATE_NETWORK_SUMMARY_TABLE = """
CREATE TABLE network_summary (
    id SERIAL PRIMARY KEY,
    total_active_stake BIGINT NOT NULL,
    total_current_stake BIGINT NOT NULL,
    total_delinquent_stake BIGINT NOT NULL,
    total_active_stake_sol DECIMAL(20, 9),
    total_validators INTEGER,
    active_validators INTEGER,
    delinquent_validators INTEGER,
    collected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

def create_validators_tables(conn):
    """
    Create the validators_data and network_summary tables if they don't exist
    
    Args:
        conn: Database connection object
    """
    with conn.cursor() as cur:
        # Check and create validators_data table
        cur.execute(CHECK_VALIDATORS_TABLE_EXISTS)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            print("Creating validators_data table...")
            cur.execute(CREATE_VALIDATORS_TABLE)
            print("Table 'validators_data' created successfully")
        else:
            print("Table 'validators_data' already exists")
        
        # Check and create network_summary table
        cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'network_summary'
        );
        """)
        
        network_table_exists = cur.fetchone()[0]
        
        if not network_table_exists:
            print("Creating network_summary table...")
            cur.execute(CREATE_NETWORK_SUMMARY_TABLE)
            print("Table 'network_summary' created successfully")
        else:
            print("Table 'network_summary' already exists")
        
        conn.commit()

def save_validators_dataframe_to_db(df: pd.DataFrame, conn, batch_size: int = 1000):
    """
    Save validators DataFrame to the database
    
    Args:
        df: Validators DataFrame
        conn: Database connection
        batch_size: Number of records to insert per batch
    """
    if df.empty:
        print("No validators data to save")
        return 0
    
    # Prepare the data for insertion
    df_copy = df.copy()
    
    # Add collection timestamp
    collection_time = datetime.now()
    df_copy['collected_at'] = collection_time
    
    # Map DataFrame columns to database columns
    column_mapping = {
        'identityPubkey': 'identity_pubkey',
        'voteAccountPubkey': 'vote_account_pubkey',
        'commission': 'commission',
        'lastVote': 'last_vote',
        'rootSlot': 'root_slot',
        'credits': 'credits',
        'epochCredits': 'epoch_credits',
        'activatedStake': 'activated_stake',
        'stake_in_sol': 'stake_in_sol',
        'version': 'version',
        'delinquent': 'delinquent',
        'skipRate': 'skip_rate',
        'is_high_commission': 'is_high_commission',
        'performance_score': 'performance_score',
        'collected_at': 'collected_at'
    }
    
    # Select and rename columns
    db_columns = []
    for df_col, db_col in column_mapping.items():
        if df_col in df_copy.columns:
            db_columns.append(db_col)
        else:
            print(f"Warning: Column {df_col} not found in DataFrame")
    
    # Rename columns to match database schema
    df_for_db = df_copy.rename(columns=column_mapping)
    df_for_db = df_for_db[db_columns]
    
    # Handle null values
    df_for_db = df_for_db.where(pd.notna(df_for_db), None)
    
    print(f"Preparing to save {len(df_for_db)} validators to database...")
    
    # Insert data in batches
    total_inserted = 0
    
    with conn.cursor() as cur:
        for i in range(0, len(df_for_db), batch_size):
            batch = df_for_db.iloc[i:i + batch_size]
            
            # Create the INSERT query
            placeholders = ', '.join(['%s'] * len(db_columns))
            insert_query = f"""
            INSERT INTO validators_data ({', '.join(db_columns)})
            VALUES ({placeholders})
            ON CONFLICT (identity_pubkey, collected_at) 
            DO UPDATE SET
                commission = EXCLUDED.commission,
                last_vote = EXCLUDED.last_vote,
                root_slot = EXCLUDED.root_slot,
                credits = EXCLUDED.credits,
                epoch_credits = EXCLUDED.epoch_credits,
                activated_stake = EXCLUDED.activated_stake,
                stake_in_sol = EXCLUDED.stake_in_sol,
                version = EXCLUDED.version,
                delinquent = EXCLUDED.delinquent,
                skip_rate = EXCLUDED.skip_rate,
                is_high_commission = EXCLUDED.is_high_commission,
                performance_score = EXCLUDED.performance_score
            """
            
            # Convert batch to list of tuples
            batch_data = [tuple(row) for row in batch.values]
            
            try:
                cur.executemany(insert_query, batch_data)
                batch_inserted = len(batch)
                total_inserted += batch_inserted
                print(f"Inserted batch {i//batch_size + 1}: {batch_inserted} records")
                
            except Exception as e:
                print(f"Error inserting batch {i//batch_size + 1}: {e}")
                conn.rollback()
                raise
    
    conn.commit()
    print(f"Successfully saved {total_inserted} validators to database")
    return total_inserted

def save_network_summary_to_db(df: pd.DataFrame, conn):
    """
    Save network summary data to database
    
    Args:
        df: Validators DataFrame with network summary in attrs
        conn: Database connection
    """
    collection_time = datetime.now()
    
    # Calculate summary statistics
    total_validators = len(df)
    active_validators = len(df[df['delinquent'] == False])
    delinquent_validators = len(df[df['delinquent'] == True])
    
    # Get network totals from DataFrame attributes or calculate from data
    total_active_stake = getattr(df, 'attrs', {}).get('totalActiveStake', df['activatedStake'].sum())
    total_current_stake = getattr(df, 'attrs', {}).get('totalCurrentStake', df['activatedStake'].sum())
    total_delinquent_stake = getattr(df, 'attrs', {}).get('totalDelinquentStake', 
                                                         df[df['delinquent'] == True]['activatedStake'].sum())
    total_active_stake_sol = total_active_stake / 1_000_000_000
    
    with conn.cursor() as cur:
        insert_query = """
        INSERT INTO network_summary (
            total_active_stake, total_current_stake, total_delinquent_stake,
            total_active_stake_sol, total_validators, active_validators,
            delinquent_validators, collected_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cur.execute(insert_query, (
            total_active_stake,
            total_current_stake,
            total_delinquent_stake,
            total_active_stake_sol,
            total_validators,
            active_validators,
            delinquent_validators,
            collection_time
        ))
    
    conn.commit()
    print(f"Network summary saved to database")

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
        
        # Add network summary info
        df = add_network_summary_info(df, validators_data)
        
        # Connect to database
        print("Connecting to database...")
        conn = get_db_connection()
        
        # Create tables if needed
        create_validators_tables(conn)
        
        # Save data
        print("Saving validators data...")
        validators_saved = save_validators_dataframe_to_db(df, conn)
        
        print("Saving network summary...")
        save_network_summary_to_db(df, conn)
        
        # Close connection
        conn.close()
        
        print(f"\n{'='*50}")
        print("DATABASE SAVE COMPLETE")
        print(f"{'='*50}")
        print(f"Validators saved: {validators_saved}")
        print(f"Network summary saved: 1 record")
        print(f"Collection timestamp: {datetime.now()}")
        
    except Exception as e:
        print(f"Error saving to database: {e}")
        raise

if __name__ == "__main__":
    import sys
    
    # Allow file path as command line argument
    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    main(file_path) 