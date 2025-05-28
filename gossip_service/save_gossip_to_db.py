from datetime import datetime
from psycopg2.extras import execute_values

# SQL query constant for inserting gossip peer data into TimescaleDB
INSERT_GOSSIP_PEERS_QUERY = """
    INSERT INTO gossip_peers (identity_key, ip_address, gossip_port, tpu_port, tpu_quic_port, timestamp)
    VALUES %s
    ON CONFLICT (identity_key, timestamp) DO UPDATE SET
        ip_address = EXCLUDED.ip_address,
        gossip_port = EXCLUDED.gossip_port,
        tpu_port = EXCLUDED.tpu_port,
        tpu_quic_port = EXCLUDED.tpu_quic_port
"""

# SQL query to create gossip_peers table if it doesn't exist
CREATE_GOSSIP_PEERS_TABLE = """
    CREATE TABLE IF NOT EXISTS gossip_peers (
        identity_key VARCHAR(44) NOT NULL,
        ip_address VARCHAR(50) NOT NULL,
        gossip_port INTEGER,
        tpu_port INTEGER,
        tpu_quic_port INTEGER,
        timestamp TIMESTAMPTZ NOT NULL,
        PRIMARY KEY (identity_key, timestamp)
    );
    
    -- Create hypertable for TimescaleDB if not already created
    SELECT create_hypertable('gossip_peers', 'timestamp', if_not_exists => TRUE);
"""

def save_data_to_db(conn, data):
    """
    Insert gossip peer data into TimescaleDB gossip_peers table as daily snapshots
    """
    # Use current date at midnight for consistent daily snapshots
    snapshot_timestamp = datetime.now().replace(second=0, microsecond=0)
    
    # First, ensure the gossip_peers table exists and is a hypertable
    try:
        with conn.cursor() as cur:
            cur.execute(CREATE_GOSSIP_PEERS_TABLE)
            conn.commit()
    except Exception as e:
        print(f"Note: Table creation/hypertable setup: {e}")
        conn.rollback()
    
    # Prepare the data for batch insert
    records = []
    for row in data:
        # Extract all required fields from the gossip data
        identity_key = row.get('Identity', row.get('identity_key'))
        ip_address = row.get('IP Address', row.get('ip_address'))
        gossip_port = row.get('Gossip Port', row.get('gossip_port'))
        tpu_port = row.get('TPU Port', row.get('tpu_port'))
        tpu_quic_port = row.get('TPU QUIC Port', row.get('tpu_quic_port'))
        
        # Skip records without required fields
        if not identity_key or not ip_address:
            continue
            
        records.append((
            identity_key,
            ip_address,
            gossip_port,
            tpu_port,
            tpu_quic_port,
            snapshot_timestamp
        ))
    
    if not records:
        print("No valid records to insert")
        return
    
    try:
        with conn.cursor() as cur:
            # Use batch insert for efficient TimescaleDB insertion
            execute_values(cur, INSERT_GOSSIP_PEERS_QUERY, records)
            
            rows_affected = cur.rowcount
            conn.commit()
            
            print(f"Inserted/updated {rows_affected} gossip peer records for {snapshot_timestamp.date()}")
    except Exception as e:
        conn.rollback()
        print(f"Error inserting gossip peer data: {e}")
        raise
