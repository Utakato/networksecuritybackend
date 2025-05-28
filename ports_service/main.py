#!/usr/bin/env python3

import nmap3
import sys
import os
from datetime import datetime

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from get_all_ip_addresses import get_all_ip_addresses
from save_open_ports_to_db import save_open_ports_to_db, save_multiple_hosts_ports
from db_service.connection import get_db_connection

# Initialize nmap
nmap = nmap3.Nmap()

def get_port_info(port):
    """
    Extract port information from nmap scan result
    
    Args:
        port (dict): Port information from nmap scan
        
    Returns:
        dict: Formatted port information
    """
    protocol = port['protocol']
    port_number = port['portid']
    service = port['service']['name']        

    new_port = {
        "protocol": protocol,
        "port": port_number,
        "service": service
    }

    return new_port

def scan_ports(ip_address):
    """
    Scan ports for a given IP address using nmap
    
    Args:
        ip_address (str): IP address to scan
        
    Returns:
        list: List of open ports
    """
    try:
        print(f"Scanning ports for {ip_address}...")
        scan_results = nmap.scan_top_ports(ip_address)

        if ip_address not in scan_results:
            print(f"No scan results for {ip_address}")
            return []

        scanned_ports = scan_results[ip_address]['ports']
        open_ports = []

        for port in scanned_ports:
            if port['state'] == 'open':
                new_port = get_port_info(port)
                open_ports.append(new_port)

        print(f"Found {len(open_ports)} open ports for {ip_address}")
        return open_ports
        
    except Exception as e:
        print(f"Error scanning {ip_address}: {e}")
        return []

def scan_and_save_single_ip(ip_data, conn):
    """
    Scan a single IP address and save results to database
    
    Args:
        ip_data (dict): Dictionary containing ip_address and identity_key
        conn: Database connection
        
    Returns:
        dict: Results of the scan and save operation
    """
    ip_address = ip_data['ip_address']
    identity_key = ip_data['identity_key']
    
    # Scan ports
    open_ports = scan_ports(ip_address)
    
    # Save to database
    saved_count = 0
    if open_ports:
        saved_count = save_open_ports_to_db(open_ports, identity_key, ip_address, conn)
        
        print(f"Results for {ip_address}:")
        for port in open_ports:
            print(f"  {port['port']}/{port['protocol']} - {port['service']}")
    else:
        print(f"No open ports found for {ip_address}")
    
    return {
        'ip_address': ip_address,
        'identity_key': identity_key,
        'open_ports': open_ports,
        'saved_count': saved_count
    }

def scan_all_ips_from_db(limit=None):
    """
    Get all IP addresses from database, scan them, and save results
    
    Args:
        limit (int): Optional limit on number of IPs to scan
    """
    print("Starting port scanning service...")
    print("=" * 50)
    
    # Get all IP addresses from database
    print("Retrieving IP addresses from gossip_peers table...")
    ip_data_list = get_all_ip_addresses()
    
    if not ip_data_list:
        print("No IP addresses found in database")
        return
    
    # Apply limit if specified
    if limit:
        ip_data_list = ip_data_list[:limit]
        print(f"Limiting scan to first {limit} IP addresses")
    
    print(f"Found {len(ip_data_list)} IP addresses to scan")
    print("=" * 50)
    
    # Connect to database
    conn = get_db_connection()
    
    try:
        total_scanned = 0
        total_ports_saved = 0
        start_time = datetime.now()
        
        for i, ip_data in enumerate(ip_data_list, 1):
            print(f"\n[{i}/{len(ip_data_list)}] Processing {ip_data['ip_address']}...")
            
            result = scan_and_save_single_ip(ip_data, conn)
            total_scanned += 1
            total_ports_saved += result['saved_count']
            
            # Progress update every 10 scans
            if i % 10 == 0:
                elapsed = datetime.now() - start_time
                print(f"\nProgress: {i}/{len(ip_data_list)} completed in {elapsed}")
                print(f"Total ports saved so far: {total_ports_saved}")
        
        # Final summary
        end_time = datetime.now()
        total_time = end_time - start_time
        
        print("\n" + "=" * 50)
        print("SCAN COMPLETE")
        print("=" * 50)
        print(f"Total IPs scanned: {total_scanned}")
        print(f"Total ports saved: {total_ports_saved}")
        print(f"Total time: {total_time}")
        print(f"Average time per IP: {total_time / total_scanned if total_scanned > 0 else 'N/A'}")
        
    except KeyboardInterrupt:
        print("\n\nScan interrupted by user")
    except Exception as e:
        print(f"\nError during scanning: {e}")
    finally:
        conn.close()
        print("Database connection closed")

def scan_specific_ips(ip_addresses):
    """
    Scan specific IP addresses (for testing)
    
    Args:
        ip_addresses (list): List of IP addresses to scan
    """
    print("Scanning specific IP addresses...")
    
    conn = get_db_connection()
    
    try:
        for ip_address in ip_addresses:
            # Create dummy identity key for testing
            identity_key = f"test_identity_{ip_address.replace('.', '_')}"
            
            ip_data = {
                'ip_address': ip_address,
                'identity_key': identity_key
            }
            
            result = scan_and_save_single_ip(ip_data, conn)
            
    finally:
        conn.close()

def main():
    """
    Main function
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Port scanning service for Solana validators')
    parser.add_argument('--limit', type=int, help='Limit number of IPs to scan')
    parser.add_argument('--test-ips', nargs='+', help='Test with specific IP addresses')
    
    args = parser.parse_args()
    
    if args.test_ips:
        scan_specific_ips(args.test_ips)
    else:
        scan_all_ips_from_db(limit=args.limit)

if __name__ == "__main__":
    main()
