#!/usr/bin/env python3
"""
Utility script to query validator information from the database
"""

import sys
import os
from typing import Optional, List, Dict, Any

# Add the parent directory to the path to import db_module
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from db_service.connection import get_db_connection

def get_validator_by_pubkey(identity_pubkey: str, conn) -> List[Dict[str, Any]]:
    """
    Get validator info by identity pubkey
    
    Args:
        identity_pubkey: The validator's identity public key
        conn: Database connection
        
    Returns:
        List of validator info records
    """
    query = """
        SELECT identity_pubkey, info_pubkey, name, details, website, 
               icon_url, keybase_username, timestamp
        FROM validator_info 
        WHERE identity_pubkey = %s
        ORDER BY timestamp DESC
    """
    
    with conn.cursor() as cur:
        cur.execute(query, (identity_pubkey,))
        results = cur.fetchall()
        
        columns = ['identity_pubkey', 'info_pubkey', 'name', 'details', 
                  'website', 'icon_url', 'keybase_username', 'timestamp']
        
        return [dict(zip(columns, row)) for row in results]

def search_validators_by_name(name_pattern: str, conn) -> List[Dict[str, Any]]:
    """
    Search validators by name pattern
    
    Args:
        name_pattern: Pattern to search for in validator names
        conn: Database connection
        
    Returns:
        List of validator info records
    """
    query = """
        SELECT DISTINCT ON (identity_pubkey) 
               identity_pubkey, info_pubkey, name, details, website, 
               icon_url, keybase_username, timestamp
        FROM validator_info 
        WHERE name ILIKE %s
        ORDER BY identity_pubkey, timestamp DESC
        LIMIT 50
    """
    
    with conn.cursor() as cur:
        cur.execute(query, (f'%{name_pattern}%',))
        results = cur.fetchall()
        
        columns = ['identity_pubkey', 'info_pubkey', 'name', 'details', 
                  'website', 'icon_url', 'keybase_username', 'timestamp']
        
        return [dict(zip(columns, row)) for row in results]

def get_validators_with_websites(conn) -> List[Dict[str, Any]]:
    """
    Get all validators that have websites
    
    Args:
        conn: Database connection
        
    Returns:
        List of validator info records with websites
    """
    query = """
        SELECT DISTINCT ON (identity_pubkey) 
               identity_pubkey, info_pubkey, name, details, website, 
               icon_url, keybase_username, timestamp
        FROM validator_info 
        WHERE website IS NOT NULL AND website != ''
        ORDER BY identity_pubkey, timestamp DESC
    """
    
    with conn.cursor() as cur:
        cur.execute(query)
        results = cur.fetchall()
        
        columns = ['identity_pubkey', 'info_pubkey', 'name', 'details', 
                  'website', 'icon_url', 'keybase_username', 'timestamp']
        
        return [dict(zip(columns, row)) for row in results]

def get_latest_validator_info(limit: int = 20, conn=None) -> List[Dict[str, Any]]:
    """
    Get the latest validator info records
    
    Args:
        limit: Number of records to return
        conn: Database connection
        
    Returns:
        List of latest validator info records
    """
    query = """
        SELECT DISTINCT ON (identity_pubkey) 
               identity_pubkey, info_pubkey, name, details, website, 
               icon_url, keybase_username, timestamp
        FROM validator_info 
        ORDER BY identity_pubkey, timestamp DESC
        LIMIT %s
    """
    
    with conn.cursor() as cur:
        cur.execute(query, (limit,))
        results = cur.fetchall()
        
        columns = ['identity_pubkey', 'info_pubkey', 'name', 'details', 
                  'website', 'icon_url', 'keybase_username', 'timestamp']
        
        return [dict(zip(columns, row)) for row in results]

def print_validator_info(validators: List[Dict[str, Any]]):
    """
    Pretty print validator information
    
    Args:
        validators: List of validator dictionaries
    """
    if not validators:
        print("No validators found.")
        return
    
    print(f"\nFound {len(validators)} validator(s):")
    print("=" * 80)
    
    for i, validator in enumerate(validators, 1):
        print(f"\n{i}. {validator['name'] or 'Unnamed Validator'}")
        print(f"   Identity: {validator['identity_pubkey']}")
        print(f"   Info Key: {validator['info_pubkey']}")
        
        if validator['details']:
            print(f"   Details: {validator['details']}")
        
        if validator['website']:
            print(f"   Website: {validator['website']}")
            
        if validator['keybase_username']:
            print(f"   Keybase: {validator['keybase_username']}")
            
        if validator['icon_url']:
            print(f"   Icon URL: {validator['icon_url']}")
            
        print(f"   Last Updated: {validator['timestamp']}")
        
        if i < len(validators):
            print("-" * 40)

def main():
    """
    Main function for the validator info query utility
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Query validator information from database')
    parser.add_argument('--pubkey', type=str, help='Get validator by identity pubkey')
    parser.add_argument('--search', type=str, help='Search validators by name')
    parser.add_argument('--websites', action='store_true', help='Show all validators with websites')
    parser.add_argument('--latest', type=int, default=20, help='Show latest validators (default: 20)')
    
    args = parser.parse_args()
    
    try:
        # Connect to database
        conn = get_db_connection()
        
        if args.pubkey:
            print(f"Searching for validator with pubkey: {args.pubkey}")
            validators = get_validator_by_pubkey(args.pubkey, conn)
            
        elif args.search:
            print(f"Searching for validators with name containing: {args.search}")
            validators = search_validators_by_name(args.search, conn)
            
        elif args.websites:
            print("Getting all validators with websites...")
            validators = get_validators_with_websites(conn)
            
        else:
            print(f"Getting latest {args.latest} validators...")
            validators = get_latest_validator_info(args.latest, conn)
        
        print_validator_info(validators)
        
        conn.close()
        
    except Exception as e:
        print(f"Error querying validator info: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 