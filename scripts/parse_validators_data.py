#!/usr/bin/env python3
"""
Script to parse validators data from JSON file into a pandas DataFrame
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
    Parse validators data into a pandas DataFrame
    
    Args:
        validators_data: Dictionary containing validators data from JSON
        
    Returns:
        pandas DataFrame with validators information
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
    
    # Convert numeric columns to appropriate types
    numeric_columns = ['commission', 'lastVote', 'rootSlot', 'credits', 'epochCredits', 'activatedStake']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Convert boolean columns
    if 'delinquent' in df.columns:
        df['delinquent'] = df['delinquent'].astype(bool)
    
    # Handle skipRate (can be null)
    if 'skipRate' in df.columns:
        df['skipRate'] = pd.to_numeric(df['skipRate'], errors='coerce')
    
    # Clean version field - handle "unknown" versions
    if 'version' in df.columns:
        df['version'] = df['version'].replace('unknown', None)
    
    # Add derived columns for analysis
    df['stake_in_sol'] = df['activatedStake'] / 1_000_000_000  # Convert lamports to SOL
    df['is_high_commission'] = df['commission'] >= 10  # Flag high commission validators
    df['performance_score'] = df['epochCredits'] / df['epochCredits'].max() if 'epochCredits' in df.columns else 0
    
    print(f"Successfully parsed {len(df)} validators")
    return df

def add_network_summary_info(df: pd.DataFrame, validators_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Add network-level summary information as metadata to the DataFrame
    
    Args:
        df: Validators DataFrame
        validators_data: Original JSON data with network summary
        
    Returns:
        DataFrame with added network metadata
    """
    # Store network summary as DataFrame attributes
    df.attrs['totalActiveStake'] = validators_data.get('totalActiveStake', 0)
    df.attrs['totalCurrentStake'] = validators_data.get('totalCurrentStake', 0)
    df.attrs['totalDelinquentStake'] = validators_data.get('totalDelinquentStake', 0)
    df.attrs['totalActiveStakeSOL'] = validators_data.get('totalActiveStake', 0) / 1_000_000_000
    
    return df

def get_data_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a summary of the parsed data
    
    Args:
        df: Validators DataFrame
        
    Returns:
        Dictionary with summary statistics
    """
    if df.empty:
        return {"error": "No data to summarize"}
    
    summary = {
        "total_validators": len(df),
        "active_validators": len(df[df['delinquent'] == False]),
        "delinquent_validators": len(df[df['delinquent'] == True]),
        "total_stake_sol": df['stake_in_sol'].sum(),
        "average_commission": df['commission'].mean(),
        "median_commission": df['commission'].median(),
        "version_distribution": df['version'].value_counts().to_dict(),
        "commission_ranges": {
            "0%": len(df[df['commission'] == 0]),
            "1-5%": len(df[(df['commission'] > 0) & (df['commission'] <= 5)]),
            "6-10%": len(df[(df['commission'] > 5) & (df['commission'] <= 10)]),
            "10%+": len(df[df['commission'] > 10])
        }
    }
    
    # Add network metadata if available
    if hasattr(df, 'attrs') and df.attrs:
        summary['network_total_active_stake_sol'] = df.attrs.get('totalActiveStakeSOL', 0)
        summary['network_delinquent_stake'] = df.attrs.get('totalDelinquentStake', 0)
    
    return summary

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
        
        # Add network summary info
        df = add_network_summary_info(df, validators_data)
        
        # Display summary
        summary = get_data_summary(df)
        print("\n" + "="*50)
        print("DATA SUMMARY")
        print("="*50)
        for key, value in summary.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for sub_key, sub_value in value.items():
                    print(f"  {sub_key}: {sub_value}")
            else:
                print(f"{key}: {value}")
        
        print(f"\nDataFrame shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        print(f"Error processing validators data: {e}")
        return None

if __name__ == "__main__":
    df = main() 