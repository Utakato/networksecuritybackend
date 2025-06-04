#!/usr/bin/env python3

import sys
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import from shared utilities
from shared_utils.data_access import get_all_ip_addresses
from shared_utils.scanning import scan_ports, get_open_ports_from_scan
from shared_utils.progress_reporting import (
    print_startup_banner, 
    print_ip_retrieval_info, 
    print_progress_update, 
    print_scan_summary
)

from save_open_ports_to_db import save_open_ports_to_db

def scan_single_ip_threaded(ip_data, verbose=False):
    """
    Scan a single IP address for open ports and save to database immediately
    
    Args:
        ip_data (dict): Dictionary containing ip_address and identity_key
        verbose (bool): Enable verbose output
        
    Returns:
        dict: Scan results with database save status
    """
    ip_address = ip_data['ip_address']
    identity_key = ip_data['identity_key']
    
    try:
        # Use shared scanning utility
        scan_result = scan_ports(ip_address, arguments="-Pn -F")
        
        if not scan_result['success']:
            if verbose:
                print(f"❌ Scan failed for {ip_address}: {scan_result['error']}")
            return {
                'ip_address': ip_address,
                'identity_key': identity_key,
                'open_ports': [],
                'ports_saved': 0,
                'scan_success': False,
                'error': scan_result['error']
            }
        
        # Extract open ports from scan data
        open_ports = get_open_ports_from_scan(scan_result, ip_address)
        
        # Save immediately to database if ports found
        ports_saved = 0
        if open_ports and len(open_ports) > 0:
            ports_saved = save_open_ports_to_db(open_ports, identity_key, ip_address)
            if verbose:
                print(f"✅ Found and saved {ports_saved} open ports for {ip_address}")
        else:
            if verbose:
                print(f"🔍 No open ports found for {ip_address}")
        
        return {
            'ip_address': ip_address,
            'identity_key': identity_key,
            'open_ports': open_ports,
            'ports_saved': ports_saved,
            'scan_success': True,
            'error': None
        }
        
    except Exception as e:
        error_msg = f"Error scanning {ip_address}: {str(e)}"
        if verbose:
            print(f"❌ {error_msg}")
        
        return {
            'ip_address': ip_address,
            'identity_key': identity_key,
            'open_ports': [],
            'ports_saved': 0,
            'scan_success': False,
            'error': error_msg
        }

def scan_all_ips_multithreaded(limit=None, max_workers=20, verbose=False):
    """
    Get all IP addresses from database, scan them using multiple threads with per-thread saving
    
    Args:
        limit (int): Optional limit on number of IPs to scan
        max_workers (int): Maximum number of concurrent threads
        verbose (bool): Enable verbose output
    """
    if verbose:
        print_startup_banner(max_workers, scan_type="port")
    
    # Get all IP addresses from database
    ip_data_list = get_all_ip_addresses()
    
    if verbose and not print_ip_retrieval_info(len(ip_data_list), limit, max_workers, scan_type="port"):
        return
    elif not verbose and len(ip_data_list) == 0:
        print("❌ No IP addresses found in database")
        return
    
    # Apply limit if specified
    if limit:
        ip_data_list = ip_data_list[:limit]
        if verbose:
            print(f"🔢 Limiting scan to first {limit} IP addresses")
    
    start_time = datetime.now()
    completed_scans = []
    failed_scans = []
    total_ports_saved = 0
    
    # Perform multithreaded scanning with per-thread saving
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="PortScanner") as executor:
        # Submit all scan jobs
        future_to_ip = {
            executor.submit(scan_single_ip_threaded, ip_data, verbose): ip_data 
            for ip_data in ip_data_list
        }
        
        # Process completed scans
        for i, future in enumerate(as_completed(future_to_ip), 1):
            ip_data = future_to_ip[future]
            try:
                result = future.result()
                
                if result['scan_success']:
                    completed_scans.append(result)
                    total_ports_saved += result['ports_saved']
                else:
                    failed_scans.append(result)
                
                # Progress update
                if verbose:
                    print_progress_update(i, len(ip_data_list), start_time, scan_type="port")
                    
            except Exception as e:
                if verbose:
                    print(f"❌ Scan failed for {ip_data['ip_address']}: {e}")
                failed_scans.append({
                    'ip_address': ip_data['ip_address'],
                    'identity_key': ip_data['identity_key'],
                    'error': str(e)
                })
    
    # Final summary (no batch saving needed - all saved during scanning)
    end_time = datetime.now()
    total_time = end_time - start_time
    
    if verbose:
        print(f"\n🎉 Port scanning complete with per-thread saving!")
        print_scan_summary(completed_scans, failed_scans, total_ports_saved, 
                          total_time, None, len(ip_data_list), scan_type="port")
    else:
        # Minimal output for non-verbose mode
        print(f"Port scan complete: {len(completed_scans)} IPs scanned, {total_ports_saved} ports saved in {total_time}") 