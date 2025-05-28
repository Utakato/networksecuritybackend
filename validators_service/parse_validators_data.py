#!/usr/bin/env python3
"""
Script to parse validators data from JSON file into a pandas DataFrame for TimescaleDB
"""

import json
import pandas as pd
from typing import Dict, List, Any
import os

def load_validators_json(file_path: str) -> Dict[str, Any]:
    """
    Load validators data from JSON file
    
    Args:
        file_path: Path to the validators JSON file
        
    Returns:
        Dictionary containing the parsed JSON data
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        print(f"Successfully loaded validators data from {file_path}")
        return data
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        raise
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file {file_path}: {e}")
        raise

def parse_validators_to_dataframe(validators_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Parse validators data into a pandas DataFrame for TimescaleDB storage
    
    Args:
        validators_data: Dictionary containing validators data from JSON
        
    Returns:
        pandas DataFrame with validators information matching TimescaleDB schema
    """
    # Extract validators list
    validators_list = validators_data.get('validators', [])
    
    if not validators_list:
        print("Warning: No validators found in data")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(validators_list)
    
    # Data type conversions and optimizations
    print("Processing data types...")
    
    # Convert numeric columns to appropriate types (matching TimescaleDB schema)
    numeric_columns = ['commission', 'lastVote', 'rootSlot', 'credits', 'epochCredits', 'activatedStake']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Convert boolean columns (delinquent -> is_delinquent for schema alignment)
    if 'delinquent' in df.columns:
        df['delinquent'] = df['delinquent'].astype(bool)
    
    # Handle skipRate (can be null, "-", or numeric/percentage)
    if 'skipRate' in df.columns:
        # Replace "-" with None, keep existing null/None values as None
        df['skipRate'] = df['skipRate'].replace('-', None)
        # Convert to numeric (handles percentages, keeps 0 as 0, preserves None as None)
        df['skipRate'] = pd.to_numeric(df['skipRate'], errors='coerce')
    
    # Clean version field - handle "unknown" versions
    if 'version' in df.columns:
        df['version'] = df['version'].replace('unknown', None)
    
    print(f"Successfully parsed {len(df)} validators")
    return df



def main():
    """
    Main function to demonstrate the parsing functionality
    """
    # Default file path (relative to project root)
    default_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'validators_data.json')
    
    try:
        # Load and parse the data
        print("Loading validators data...")
        validators_data = load_validators_json(default_file_path)
        
        print("Parsing to DataFrame...")
        df = parse_validators_to_dataframe(validators_data)
        
        if df.empty:
            print("No data to process")
            return None

        return df
        
    except Exception as e:
        print(f"Error processing validators data: {e}")
        return None

if __name__ == "__main__":
    df = main() 