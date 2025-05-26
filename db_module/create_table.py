# SQL Query Constants
CHECK_TABLE_EXISTS_QUERY = """
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'gossip_data'
);
"""

CREATE_TABLE_QUERY = """
CREATE TABLE gossip_data (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(50) NOT NULL,
    identity VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    collected_at TIMESTAMP NOT NULL,
    UNIQUE(ip_address, identity)
);
"""

def create_table_if_not_exists(conn):
    """
    Create the gossip_data table if it doesn't exist
    """
    with conn.cursor() as cur:
        # Check if table exists
        cur.execute(CHECK_TABLE_EXISTS_QUERY)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            print("Creating gossip_data table...")
            cur.execute(CREATE_TABLE_QUERY)
            conn.commit()
            print("Table 'gossip_data' created successfully")
        else:
            print("Table 'gossip_data' already exists")
