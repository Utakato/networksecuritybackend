#!/usr/bin/env python3

import pandas as pd
import json

# json to DataFrame
def parse_gossip_data(filename):
    # Read the JSON file
    with open(filename, 'r') as file:
        data = json.load(file)
    
    # Handle both single object and array of objects
    if isinstance(data, dict):
        data = [data]
    elif not isinstance(data, list):
        raise ValueError("JSON data must be either an object or an array of objects")
    
    # Create a pandas DataFrame from JSON data
    df = pd.DataFrame(data)
    
    # Extract only the columns we're interested in and map to expected names
    result_df = df[['ipAddress', 'identityPubkey', 'version']].copy()
    result_df.columns = ['IP Address', 'Identity', 'Version']
    
    return result_df

def main():
    # Parse the data
    result = parse_gossip_data('../data/gossip_data.json')
    
    # Save to CSV
    result.to_csv('gossip_extracted.csv', index=False)
    print(f"Saved {len(result)} rows to gossip_extracted.csv")
    
    # Analyze versions
    print("\nVersion distribution:")
    version_counts = result['Version'].value_counts()
    print(version_counts.head(10))  # Print top 10 versions

if __name__ == "__main__":
    main() 