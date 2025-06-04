#!/usr/bin/env python3

import sys
import os
from datetime import datetime
from psycopg2.extras import execute_values

# Add the parent directory to the path to import db_module
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from db_service.connection import get_db_connection

# SQL query for inserting open ports data into TimescaleDB
INSERT_OPEN_PORTS_QUERY = """
    INSERT INTO ip_open_ports (ip_address, identity_key, protocol, port, service, timestamp)
    VALUES %s
"""

def create_ip_open_ports_table(conn):
    """
    Create the ip_open_ports table if it doesn't exist
    
    Args:
        conn: Database connection
    """
    try:
        with conn.cursor() as cur:
            # Create table first without unique constraint
            create_table_query = """
                CREATE TABLE IF NOT EXISTS ip_open_ports (
                    ip_address VARCHAR(50) NOT NULL,
                    identity_key VARCHAR(44) NOT NULL,
                    protocol VARCHAR(10) NOT NULL,
                    port INTEGER NOT NULL,
                    service VARCHAR(100),
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """
            cur.execute(create_table_query)
            conn.commit()  # Commit table creation first
            
        # Add unique constraint in separate transaction
        try:
            with conn.cursor() as cur:
                add_constraint_query = """
                    ALTER TABLE ip_open_ports 
                    ADD CONSTRAINT ip_open_ports_unique 
                    UNIQUE (ip_address, port, protocol, timestamp);
                """
                cur.execute(add_constraint_query)
                conn.commit()
        except Exception as constraint_error:
            conn.rollback()  # Rollback failed constraint addition
            # Constraint might already exist, that's fine
            if "already exists" not in str(constraint_error):
                print(f"Note: Could not add unique constraint: {constraint_error}")
        
        # Create hypertable for TimescaleDB in separate transaction
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT create_hypertable('ip_open_ports', 'timestamp', if_not_exists => TRUE);")
                conn.commit()
        except Exception as hypertable_error:
            conn.rollback()  # Rollback failed hypertable creation
            # Hypertable might already exist or TimescaleDB not available
            print(f"Note: Hypertable setup: {hypertable_error}")
        
        # Create index in separate transaction
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_ip_open_ports_lookup 
                    ON ip_open_ports (ip_address, identity_key, timestamp DESC);
                """)
                conn.commit()
                print("ip_open_ports table created/verified successfully")
        except Exception as index_error:
            conn.rollback()
            print(f"Note: Index creation: {index_error}")
            
    except Exception as e:
        print(f"Error creating ip_open_ports table: {e}")
        conn.rollback()
        raise

def save_open_ports_to_db(open_ports, identity_key, ip_address, conn=None, clean_old=True):
    """
    Save open ports data to the ip_open_ports table
    
    Args:
        open_ports (list): List of dictionaries containing port information
        identity_key (str): Identity key of the validator
        ip_address (str): IP address of the validator
        conn: Database connection (optional, will create new if not provided)
        clean_old (bool): Whether to remove old entries for this IP before inserting new ones
    
    Returns:
        int: Number of ports saved
    """
    should_close_conn = False
    
    if conn is None:
        conn = get_db_connection()
        should_close_conn = True
    
    try:
        # Ensure table exists
        create_ip_open_ports_table(conn)
        
        if not open_ports or len(open_ports) == 0:
            print(f"🔍 No open ports to save for {ip_address} (received {len(open_ports) if open_ports else 0} ports)")
            return 0
        
        # Use current timestamp for all ports in this scan
        scan_timestamp = datetime.now()
        
        # Optionally clean old entries for this IP and identity key from today
        if clean_old:
            with conn.cursor() as cur:
                # Delete entries from today for this IP/identity combination
                delete_query = """
                    DELETE FROM ip_open_ports 
                    WHERE ip_address = %s 
                    AND identity_key = %s 
                    AND timestamp::date = %s::date
                """
                cur.execute(delete_query, (ip_address, identity_key, scan_timestamp))
                deleted_count = cur.rowcount
                if deleted_count > 0:
                    print(f"Cleaned {deleted_count} old entries for {ip_address}")
        
        # Prepare records for batch insert
        records = []
        for port in open_ports:
            records.append((
                ip_address,
                identity_key,
                port['protocol'],
                int(port['port']),
                port['service'],
                scan_timestamp
            ))
        
        # Insert data using execute_values for efficiency
        with conn.cursor() as cur:
            execute_values(cur, INSERT_OPEN_PORTS_QUERY, records)
            rows_affected = cur.rowcount
            conn.commit()
            
            print(f"Saved {rows_affected} open ports for {ip_address} (Identity: {identity_key[:8]}...)")
            return rows_affected
            
    except Exception as e:
        print(f"Error saving open ports to database: {e}")
        conn.rollback()
        return 0
    finally:
        if should_close_conn and conn:
            conn.close()

def save_multiple_hosts_ports(hosts_ports_data, conn=None, clean_old=True):
    """
    Save open ports data for multiple hosts
    
    Args:
        hosts_ports_data (list): List of dictionaries containing:
            - ip_address: IP address
            - identity_key: Identity key
            - open_ports: List of open ports
        conn: Database connection (optional)
        clean_old (bool): Whether to remove old entries before inserting new ones
    
    Returns:
        int: Total number of ports saved
    """
    should_close_conn = False
    
    if conn is None:
        conn = get_db_connection()
        should_close_conn = True
    
    try:
        # Ensure table exists
        create_ip_open_ports_table(conn)
        
        total_saved = 0
        scan_timestamp = datetime.now()
        
        # Optionally clean old entries for all IPs from today
        if clean_old:
            with conn.cursor() as cur:
                for host_data in hosts_ports_data:
                    delete_query = """
                        DELETE FROM ip_open_ports 
                        WHERE ip_address = %s 
                        AND identity_key = %s 
                        AND timestamp::date = %s::date
                    """
                    cur.execute(delete_query, (
                        host_data['ip_address'], 
                        host_data['identity_key'], 
                        scan_timestamp
                    ))
        
        # Prepare all records for batch insert
        all_records = []
        for host_data in hosts_ports_data:
            ip_address = host_data['ip_address']
            identity_key = host_data['identity_key']
            open_ports = host_data['open_ports']
            
            for port in open_ports:
                all_records.append((
                    ip_address,
                    identity_key,
                    port['protocol'],
                    int(port['port']),
                    port['service'],
                    scan_timestamp
                ))
        
        if not all_records:
            print("No open ports to save for any hosts")
            return 0
        
        # Insert all data in one batch for efficiency
        with conn.cursor() as cur:
            execute_values(cur, INSERT_OPEN_PORTS_QUERY, all_records)
            rows_affected = cur.rowcount
            conn.commit()
            
            print(f"Saved {rows_affected} total open ports for {len(hosts_ports_data)} hosts")
            return rows_affected
            
    except Exception as e:
        print(f"Error saving multiple hosts ports to database: {e}")
        conn.rollback()
        return 0
    finally:
        if should_close_conn and conn:
            conn.close()

