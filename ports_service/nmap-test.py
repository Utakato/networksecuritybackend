#!/usr/bin/env python3
"""
DEPRECATED: This file has been refactored into separate modules.

The functionality has been split into:
1. get_all_ip_addresses.py - Gets IP addresses and identity keys from gossip_peers table
2. save_open_ports_to_db.py - Saves open ports to ip_open_ports table  
3. main.py - Main orchestration script that combines scanning and saving

Use main.py instead of this file.

Example usage:
    python main.py                    # Scan all IPs from database
    python main.py --limit 10         # Scan first 10 IPs only
    python main.py --test-ips 8.8.8.8 1.1.1.1  # Test with specific IPs
"""

import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def main():
    print(__doc__)
    print("\nTo run the port scanning service, use:")
    print("python main.py")
    print("\nFor help with options:")
    print("python main.py --help")

if __name__ == "__main__":
    main()

# Original code below for reference (commented out)
"""
import nmap3


nmap = nmap3.Nmap()

ip_addresses = [
    '109.94.96.39',
    '85.195.75.249',
    '80.76.51.121',
    '5.199.172.191',
    '134.119.194.129',
]

def get_port_info(port):
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
    scan_results = nmap.scan_top_ports(ip_address)

    scanned_ports = scan_results[ip_address]['ports']

    open_ports = []

    for port in scanned_ports:
        if port['state'] == 'open':
            new_port = get_port_info(port)
            open_ports.append(new_port)

    return open_ports



def scan_all_ips(ip_addresses):
    for ip_address in ip_addresses:
        open_ports = scan_ports(ip_address)
        print(f"Open ports for {ip_address}:")
        for port in open_ports:
            print(f"{port['port']}------{port['service']}-----{port['protocol']}")


scan_all_ips(ip_addresses)

def save_ports_to_db(open_ports, identity_key, ip_address):
    for port in open_ports:
        print(f"{port['port']}------{port['service']}-----{port['protocol']}")



# Scanned
# open ports
# runtime


# table ports_scans
# runtime/ with timetable extension postgress? -> check out
# identity_key
"""
