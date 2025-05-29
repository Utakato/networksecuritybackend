#!/usr/bin/env python3

import sys
import os

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from multithreaded_scanner import scan_all_ips_multithreaded

def main():
    """
    Main function
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='🔍 Port scanning service for Solana validators')
    parser.add_argument('--limit', type=int, help='Limit number of IPs to scan')
    parser.add_argument('--threads', type=int, default=20, help='Number of concurrent threads (default: 20)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    scan_all_ips_multithreaded(limit=args.limit, max_workers=args.threads, verbose=args.verbose)

if __name__ == "__main__":
    main()
