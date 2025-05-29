#!/usr/bin/env python3

import nmap3
import threading
import time

# Thread-local storage for nmap instances
thread_local = threading.local()

def get_nmap():
    """Get thread-local nmap instance"""
    if not hasattr(thread_local, 'nmap'):
        thread_local.nmap = nmap3.Nmap()
    return thread_local.nmap

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

def scan_ports(ip_address, verbose=False):
    """
    Scan ports for a given IP address using nmap (thread-safe)
    
    Args:
        ip_address (str): IP address to scan
        verbose (bool): Enable verbose output
        
    Returns:
        list: List of open ports
    """
    try:
        nmap = get_nmap()  # Get thread-local nmap instance
        thread_name = threading.current_thread().name
        
        if verbose:
            print(f"[{thread_name}] Scanning {ip_address}...")
        
        scan_results = nmap.scan_top_ports(ip_address)

        if ip_address not in scan_results:
            if verbose:
                print(f"[{thread_name}] No scan results for {ip_address}")
            return []

        scanned_ports = scan_results[ip_address]['ports']
        open_ports = []

        for port in scanned_ports:
            if port['state'] == 'open':
                new_port = get_port_info(port)
                open_ports.append(new_port)

        if verbose:
            print(f"[{thread_name}] Found {len(open_ports)} open ports for {ip_address}")
        return open_ports
        
    except Exception as e:
        thread_name = threading.current_thread().name
        if verbose:
            print(f"[{thread_name}] Error scanning {ip_address}: {e}")
        return []

def scan_single_ip_threaded(ip_data, verbose=False):
    """
    Scan a single IP address and return results (for threading)
    Database saving is done separately to avoid connection issues
    
    Args:
        ip_data (dict): Dictionary containing ip_address and identity_key
        verbose (bool): Enable verbose output
        
    Returns:
        dict: Results of the scan operation
    """
    ip_address = ip_data['ip_address']
    identity_key = ip_data['identity_key']
    
    start_time = time.time()
    
    # Scan ports
    open_ports = scan_ports(ip_address, verbose)
    
    scan_time = time.time() - start_time
    
    result = {
        'ip_address': ip_address,
        'identity_key': identity_key,
        'open_ports': open_ports,
        'scan_time': scan_time,
        'success': True
    }
    
    return result 