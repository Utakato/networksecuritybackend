#!/usr/bin/env python3

import csv
import json
import argparse
import ipaddress
from collections import Counter


class GossipDataAnalyzer:
    def __init__(self, filename):
        self.filename = filename
        self.data = self.parse_file()
        
    def parse_file(self):
        # Read the file as text
        with open(self.filename, 'r') as file:
            lines = file.readlines()
        
        # Parse the header
        header = [col.strip() for col in lines[0].split('|')]
        
        # Extract data (skip header and separator line)
        data = []
        for line in lines[2:]:
            if line.strip():  # Skip empty lines
                columns = [col.strip() for col in line.split('|')]
                if len(columns) == len(header):
                    entry = {header[i]: columns[i] for i in range(len(header))}
                    data.append(entry)
        
        return data
    
    def filter_by_version(self, version=None, min_version=None, max_version=None):
        """Filter data by exact version or version range"""
        result = self.data.copy()
        
        if version:
            result = [entry for entry in result if entry['Version'] == version]
        
        if min_version:
            result = [entry for entry in result if self._compare_versions(entry['Version'], min_version) >= 0]
        
        if max_version:
            result = [entry for entry in result if self._compare_versions(entry['Version'], max_version) <= 0]
            
        return result
    
    def filter_by_ip_range(self, ip_range):
        """Filter data by IP address range (CIDR notation)"""
        network = ipaddress.ip_network(ip_range)
        return [entry for entry in self.data if ipaddress.ip_address(entry['IP Address']) in network]
    
    def get_version_stats(self):
        """Get statistics about versions"""
        counter = Counter(entry['Version'] for entry in self.data)
        return counter
    
    def export_to_csv(self, data, output_file):
        """Export data to CSV"""
        if not data:
            print("No data to export")
            return
            
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        print(f"Exported {len(data)} entries to {output_file}")
    
    def export_to_json(self, data, output_file):
        """Export data to JSON"""
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Exported {len(data)} entries to {output_file}")
    
    def _compare_versions(self, v1, v2):
        """Compare two version strings"""
        v1_parts = [int(part) for part in v1.split('.')]
        v2_parts = [int(part) for part in v2.split('.')]
        
        # Pad with zeros if lengths differ
        while len(v1_parts) < len(v2_parts):
            v1_parts.append(0)
        while len(v2_parts) < len(v1_parts):
            v2_parts.append(0)
        
        for i in range(len(v1_parts)):
            if v1_parts[i] > v2_parts[i]:
                return 1
            elif v1_parts[i] < v2_parts[i]:
                return -1
        
        return 0


def main():
    parser = argparse.ArgumentParser(description='Analyze gossip data')
    parser.add_argument('--input', default='gossip_data.json', help='Input file')
    parser.add_argument('--output', help='Output file')
    parser.add_argument('--format', choices=['csv', 'json'], default='csv', help='Output format')
    parser.add_argument('--version', help='Filter by exact version')
    parser.add_argument('--min-version', help='Filter by minimum version')
    parser.add_argument('--max-version', help='Filter by maximum version')
    parser.add_argument('--ip-range', help='Filter by IP range (CIDR notation)')
    parser.add_argument('--stats', action='store_true', help='Show version statistics')
    
    args = parser.parse_args()
    
    analyzer = GossipDataAnalyzer(args.input)
    
    # Apply filters
    filtered_data = analyzer.data
    
    if args.version or args.min_version or args.max_version:
        filtered_data = analyzer.filter_by_version(args.version, args.min_version, args.max_version)
    
    if args.ip_range:
        filtered_data = analyzer.filter_by_ip_range(args.ip_range)
    
    # Show statistics if requested
    if args.stats:
        stats = analyzer.get_version_stats()
        print("Version distribution:")
        for version, count in stats.most_common():
            print(f"{version}: {count}")
    
    # Export data if output file is specified
    if args.output:
        if args.format == 'csv':
            analyzer.export_to_csv(filtered_data, args.output)
        else:
            analyzer.export_to_json(filtered_data, args.output)
    elif not args.stats:
        # Print first 10 entries
        print(f"Found {len(filtered_data)} entries. First 10:")
        for i, entry in enumerate(filtered_data[:10]):
            print(f"{entry['IP Address']} | {entry['Identity']} | {entry['Version']}")


if __name__ == "__main__":
    main() 