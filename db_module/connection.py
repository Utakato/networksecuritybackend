import os
import psycopg2
import dotenv

dotenv.load_dotenv()

def get_db_connection():
    """
    Create a database connection using environment variables or default values
    """
    # Get connection parameters from environment variables or use default values
    db_params = {
        'dbname': os.getenv('POSTGRES_DB', 'validator_security'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'password'),
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432')
    }
    
    # Print connection info (remove in production)
    print(f"Connecting to PostgreSQL at {db_params['host']}:{db_params['port']}")
    print(f"Database: {db_params['dbname']}, User: {db_params['user']}")
    
    try:
        # First try to connect to the specific database
        conn = psycopg2.connect(**db_params)
        return conn
    except psycopg2.OperationalError as e:
        if 'database "validator_security" does not exist' in str(e):
            # Connect to default postgres database to create our database
            print(f"Database {db_params['dbname']} does not exist. Creating it...")
            temp_params = db_params.copy()
            temp_params['dbname'] = 'postgres'
            
            conn = psycopg2.connect(**temp_params)
            conn.autocommit = True  # Needed for CREATE DATABASE
            
            with conn.cursor() as cur:
                try:
                    cur.execute(f"CREATE DATABASE {db_params['dbname']}")
                    print(f"Database {db_params['dbname']} created successfully")
                except psycopg2.Error as e:
                    print(f"Error creating database: {e}")
                    raise
            
            conn.close()
            
            # Connect to the newly created database
            return psycopg2.connect(**db_params)
        else:
            # Some other connection error
            print(f"Database connection error: {e}")
            raise
