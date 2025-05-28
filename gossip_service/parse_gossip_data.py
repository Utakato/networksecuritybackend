#!/usr/bin/env python3

import json


def parse_gossip_data_for_db(filename):
    """
    Parse gossip data from JSON file and return as list of dictionaries
    suitable for direct database insertion
    """
    # Read the JSON file
    with open(filename, 'r') as file:
        data = json.load(file)
    
    # Handle both single object and array of objects
    if isinstance(data, dict):
        data = [data]
    elif not isinstance(data, list):
        raise ValueError("JSON data must be either an object or an array of objects")
    
    # Extract and transform the data
    result = []
    for item in data:
        if all(key in item for key in ['ipAddress', 'identityPubkey', 'version']):
            result.append({
                'IP Address': item['ipAddress'],
                'Identity': item['identityPubkey'],
                'Version': item['version']
            })
    
    return result
