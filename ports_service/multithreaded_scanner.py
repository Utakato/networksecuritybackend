#!/usr/bin/env python3

import sys
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from get_all_ip_addresses import get_all_ip_addresses
from save_open_ports_to_db import save_multiple_hosts_ports
from port_scanner import scan_single_ip_threaded
from progress_reporter import print_startup_banner, print_ip_retrieval_info, print_progress_update, print_scan_summary

def scan_all_ips_multithreaded(limit=None, max_workers=20, verbose=False):
    """
    Get all IP addresses from database, scan them using multiple threads, and save results
    
    Args:
        limit (int): Optional limit on number of IPs to scan
        max_workers (int): Maximum number of concurrent threads
        verbose (bool): Enable verbose output
    """
    if verbose:
        print_startup_banner(max_workers)
    
    # Get all IP addresses from database
    ip_data_list = get_all_ip_addresses()
    
    if verbose and not print_ip_retrieval_info(len(ip_data_list), limit, max_workers):
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
    
    # Perform multithreaded scanning
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="Scanner") as executor:
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
                completed_scans.append(result)
                
                # Progress update
                if verbose:
                    print_progress_update(i, len(ip_data_list), start_time)
                    
            except Exception as e:
                if verbose:
                    print(f"❌ Scan failed for {ip_data['ip_address']}: {e}")
                failed_scans.append(ip_data)
    
    # Save all results to database in batches
    if verbose:
        print(f"\n💾 Scanning complete! Saving {len(completed_scans)} results to database...")
    save_start = datetime.now()
    
    # Prepare data for batch save
    hosts_with_ports = [
        {
            'ip_address': result['ip_address'],
            'identity_key': result['identity_key'],
            'open_ports': result['open_ports']
        }
        for result in completed_scans if result['open_ports']
    ]
    
    total_ports_saved = 0
    if hosts_with_ports:
        total_ports_saved = save_multiple_hosts_ports(hosts_with_ports)
    
    # Final summary
    end_time = datetime.now()
    total_time = end_time - start_time
    save_time = end_time - save_start
    
    if verbose:
        print_scan_summary(completed_scans, failed_scans, total_ports_saved, 
                          total_time, save_time, len(ip_data_list))
    else:
        # Minimal output for non-verbose mode
        print(f"Scan complete: {len(completed_scans)} IPs scanned, {total_ports_saved} ports saved in {total_time}") 