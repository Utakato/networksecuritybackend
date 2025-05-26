#!/usr/bin/env python3

import csv

def gossip_data_to_csv(filename):
    # Read the file as text
    with open(filename, 'r') as file:
        lines = file.readlines()
    
    # Parse the header
    header = [col.strip() for col in lines[0].split('|')]
    
    # Find indexes of the columns we want
    ip_idx = header.index('IP Address')
    identity_idx = header.index('Identity')
    version_idx = header.index('Version')
    
    # Extract data (skip header and separator line)
    extracted_data = []
    for line in lines[2:]:
        if line.strip():  # Skip empty lines
            columns = [col.strip() for col in line.split('|')]
            if len(columns) >= max(ip_idx, identity_idx, version_idx) + 1:
                extracted_data.append({
                    'IP Address': columns[ip_idx],
                    'Identity': columns[identity_idx],
                    'Version': columns[version_idx]
                })
    
    with open('../data/gossip_extracted_simple.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['IP Address', 'Identity', 'Version'])
        writer.writeheader()
        writer.writerows(extracted_data)
    

