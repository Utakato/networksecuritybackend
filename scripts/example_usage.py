#!/usr/bin/env python3
"""
Example script demonstrating how to use the validators data parsing and database saving functionality
"""

import os
import sys

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from scripts.parse_validators_data import (
    load_validators_json, 
    parse_validators_to_dataframe, 
    add_network_summary_info,
    get_data_summary
)
from scripts.save_validators_to_db import main as save_to_db

def main():
    """
    Example usage of the validators data processing pipeline
    """
    print("VALIDATORS DATA PROCESSING EXAMPLE")
    print("=" * 50)
    
    # Step 1: Parse data to DataFrame
    print("\n1. PARSING JSON TO DATAFRAME")
    print("-" * 30)
    
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'validators_data.json')
    
    try:
        # Load JSON data
        validators_data = load_validators_json(file_path)
        
        # Parse to DataFrame
        df = parse_validators_to_dataframe(validators_data)
        
        # Add network summary
        df = add_network_summary_info(df, validators_data)
        
        # Show summary
        summary = get_data_summary(df)
        print(f"Parsed {len(df)} validators successfully")
        print(f"Active validators: {summary['active_validators']}")
        print(f"Delinquent validators: {summary['delinquent_validators']}")
        print(f"Average commission: {summary['average_commission']:.2f}%")
        
        # Step 2: Show DataFrame info
        print("\n2. DATAFRAME INFORMATION")
        print("-" * 30)
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print("\nFirst 3 rows:")
        print(df[['identityPubkey', 'commission', 'delinquent', 'stake_in_sol', 'version']].head(3))
        
        # Step 3: Save to database
        print("\n3. SAVING TO DATABASE")
        print("-" * 30)
        save_to_db(file_path)
        
        print("\n✅ PROCESSING COMPLETE!")
        print("You can now query the database to analyze the validators data.")
        
        # Step 4: Show some analysis examples
        print("\n4. QUICK ANALYSIS EXAMPLES")
        print("-" * 30)
        
        # Top 10 validators by stake
        top_validators = df.nlargest(10, 'stake_in_sol')[['identityPubkey', 'stake_in_sol', 'commission', 'delinquent']]
        print("\nTop 10 validators by stake:")
        print(top_validators.to_string(index=False))
        
        # Commission distribution
        print(f"\nCommission distribution:")
        commission_dist = df['commission'].value_counts().sort_index()
        for commission, count in commission_dist.head(10).items():
            print(f"  {commission}%: {count} validators")
        
        # Version distribution
        print(f"\nVersion distribution:")
        version_dist = df['version'].value_counts()
        for version, count in version_dist.items():
            if version is not None:
                print(f"  {version}: {count} validators")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 