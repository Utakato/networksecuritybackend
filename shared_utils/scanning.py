#!/usr/bin/env python3

import nmap3
import threading
import xml.etree.ElementTree as ET

# Thread-local storage for nmap instances
_thread_local = threading.local()

def get_nmap():
    """
    Get a thread-local nmap instance
    
    Returns:
        nmap3.Nmap: Thread-safe nmap instance
    """
    if not hasattr(_thread_local, 'nm'):
        _thread_local.nm = nmap3.Nmap()
    return _thread_local.nm

def scan_ports(ip_address, arguments="-Pn -F", timeout=30):
    """
    Generic port scanning function using nmap3
    
    Args:
        ip_address (str): IP address to scan
        arguments (str): nmap arguments for scanning
        timeout (int): Timeout for scan in seconds
        
    Returns:
        dict: Scan results in dictionary format
    """
    try:
        nm = get_nmap()
        print(f"Scanning ports for {ip_address} with args: {arguments}")
        
        # Add timeout to arguments if not already present
        if '--host-timeout' not in arguments:
            arguments = f"{arguments} --host-timeout {timeout}s"
        
        # Perform the scan using nmap3 - returns XML Element
        xml_result = nm.scan_command(target=ip_address, arg=arguments)
        
        if xml_result is None:
            raise Exception("No scan result returned from nmap")
        
        return {
            'success': True,
            'ip_address': ip_address,
            'xml_data': xml_result,
            'error': None
        }
        
    except Exception as e:
        print(f"❌ Primary scan failed for {ip_address}: {str(e)}")
        
        # Try fallback method with scan_top_ports
        try:
            print(f"🔄 Trying fallback scan for {ip_address}")
            nm = get_nmap()
            
            # Use scan_top_ports as fallback - scan top 100 ports
            result = nm.scan_top_ports(ip_address, default=100)
            
            if result and ip_address in result:
                # Convert to XML-like structure for compatibility
                host_data = result[ip_address]
                if 'ports' in host_data:
                    return {
                        'success': True,
                        'ip_address': ip_address,
                        'xml_data': None,  # No XML for fallback
                        'json_data': result,  # Store JSON data instead
                        'error': None
                    }
            
            raise Exception("No data returned from fallback scan")
            
        except Exception as fallback_error:
            error_msg = f"Error scanning {ip_address}: Primary failed ({str(e)}), Fallback failed ({str(fallback_error)})"
            print(f"❌ {error_msg}")
            
            return {
                'success': False,
                'ip_address': ip_address,
                'xml_data': None,
                'error': error_msg
            }

def get_open_ports_from_xml(xml_element, ip_address):
    """
    Extract open ports from nmap XML results
    
    Args:
        xml_element: XML Element from nmap3 scan
        ip_address (str): IP address that was scanned
        
    Returns:
        list: List of open ports with details in the format expected by save_open_ports_to_db
    """
    open_ports = []
    
    try:
        # Find all ports in the XML
        for port_elem in xml_element.findall('.//port'):
            port_num = port_elem.get('portid')
            protocol = port_elem.get('protocol', 'tcp')
            
            # Check if port is open
            state_elem = port_elem.find('state')
            if state_elem is not None and state_elem.get('state') == 'open':
                # Get service information
                service_elem = port_elem.find('service')
                service_name = 'unknown'
                if service_elem is not None:
                    service_name = service_elem.get('name', 'unknown')
                
                open_ports.append({
                    'port': int(port_num),
                    'protocol': protocol,
                    'service': service_name
                })
                        
    except Exception as e:
        print(f"Error parsing XML data for {ip_address}: {e}")
    
    return open_ports

def get_open_ports_from_scan(scan_result, ip_address):
    """
    Extract open ports from scan result (backward compatibility wrapper)
    
    Args:
        scan_result (dict): Scan result from scan_ports function
        ip_address (str): IP address that was scanned
        
    Returns:
        list: List of open ports
    """
    if not scan_result.get('success'):
        return []
    
    # Try XML data first (primary scan method)
    if scan_result.get('xml_data'):
        return get_open_ports_from_xml(scan_result['xml_data'], ip_address)
    
    # Try JSON data (fallback scan method)
    elif scan_result.get('json_data'):
        return get_open_ports_from_json(scan_result['json_data'], ip_address)
    
    return []

def get_open_ports_from_json(json_data, ip_address):
    """
    Extract open ports from nmap3 JSON results (fallback method)
    
    Args:
        json_data (dict): JSON data from nmap3 scan_top_ports
        ip_address (str): IP address that was scanned
        
    Returns:
        list: List of open ports with details
    """
    open_ports = []
    
    try:
        if ip_address in json_data:
            host_data = json_data[ip_address]
            
            if 'ports' in host_data:
                for port_info in host_data['ports']:
                    if port_info.get('state') == 'open':
                        open_ports.append({
                            'port': int(port_info.get('portid', 0)),
                            'protocol': port_info.get('protocol', 'tcp'),
                            'service': port_info.get('service', {}).get('name', 'unknown')
                        })
                        
    except Exception as e:
        print(f"Error parsing JSON data for {ip_address}: {e}")
    
    return open_ports 