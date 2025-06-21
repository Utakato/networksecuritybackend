#!/usr/bin/env python3

from datetime import datetime, timedelta

def print_startup_banner(max_workers, scan_type="scan", service_name=None):
    """
    Print startup banner with configuration details
    
    Args:
        max_workers (int): Number of worker threads
        scan_type (str): Type of scan ('port', 'vulnerability', or custom)
        service_name (str): Optional custom service name
    """
    # Map scan types to emojis and names
    type_mapping = {
        "port": {"emoji": "🔍", "name": "Port Scanner"},
        "vulnerability": {"emoji": "🛡️", "name": "Vulnerability Scanner"},
        "score": {"emoji": "🔐", "name": "Security Score Calculator"},
        "scan": {"emoji": "🚀", "name": "Scanner"}
    }
    
    config = type_mapping.get(scan_type, {"emoji": "🚀", "name": "Scanner"})
    if service_name:
        config["name"] = service_name
    
    print("\n" + "="*60)
    print(f"{config['emoji']} SOLANA VALIDATOR {config['name'].upper()}")
    print("="*60)
    print(f"🧵 Worker threads: {max_workers}")
    
    if scan_type == "vulnerability":
        print("🎯 Scan mode: Vulnerability detection using nmap scripts")
    elif scan_type == "port":
        print("🎯 Scan mode: Port detection")
    elif scan_type == "score":
        print("🎯 Calculation mode: Security score based on ports & vulnerabilities")
    else:
        print(f"🎯 Scan mode: {scan_type}")
    
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

def print_ip_retrieval_info(total_ips, limit=None, max_workers=None, scan_type="scan"):
    """
    Print information about IP retrieval and validate scan parameters
    
    Args:
        total_ips (int): Total number of IPs retrieved
        limit (int): Optional limit on IPs to scan
        max_workers (int): Number of worker threads
        scan_type (str): Type of scan for customized messaging
        
    Returns:
        bool: True if scan should continue, False otherwise
    """
    print("📡 Retrieving IP addresses from gossip_peers table...")
    
    if total_ips == 0:
        print("❌ No IP addresses found in database")
        return False
    
    ips_to_scan = min(total_ips, limit) if limit else total_ips
    
    print(f"\n📊 Scan Configuration:")
    print(f"   • Total IPs in database: {total_ips}")
    print(f"   • IPs to scan: {ips_to_scan}")
    
    if max_workers:
        print(f"   • Worker threads: {max_workers}")
        print(f"   • Estimated completion: ~{estimate_completion_time(ips_to_scan, max_workers, scan_type)}")
    
    if limit:
        print(f"🔢 Limiting scan to first {limit} IP addresses")
    
    print()
    return True

def estimate_completion_time(total_ips, max_workers, scan_type="scan"):
    """
    Estimate scan completion time based on scan type
    
    Args:
        total_ips (int): Total number of IPs to scan
        max_workers (int): Number of worker threads  
        scan_type (str): Type of scan to estimate timing
        
    Returns:
        str: Formatted time estimate
    """
    # Different scan types have different average times
    avg_times = {
        "port": 15,  # seconds per IP
        "vulnerability": 45,  # vulnerability scans take longer
        "score": 2,  # score calculation is much faster
        "scan": 20  # default
    }
    
    avg_scan_time = avg_times.get(scan_type, 20)
    total_seconds = (total_ips * avg_scan_time) / max_workers
    estimated_time = timedelta(seconds=int(total_seconds))
    
    # Format the time nicely
    hours = estimated_time.seconds // 3600
    minutes = (estimated_time.seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m"
    else:
        return f"{estimated_time.seconds}s"

def print_progress_update(completed, total, start_time, scan_type="scan", interval=10):
    """
    Print progress update during scanning
    
    Args:
        completed (int): Number of completed scans
        total (int): Total number of scans
        start_time (datetime): When scanning started
        scan_type (str): Type of scan ('port', 'vulnerability', etc.)
        interval (int): Print progress every N completed items
    """
    if completed % interval == 0 or completed == total:
        progress_percent = (completed / total) * 100
        elapsed = datetime.now() - start_time
        
        # Calculate ETA
        if completed > 0:
            avg_time_per_scan = elapsed.total_seconds() / completed
            remaining_scans = total - completed
            eta_seconds = avg_time_per_scan * remaining_scans
            eta = timedelta(seconds=int(eta_seconds))
        else:
            eta = timedelta(0)
        
        # Map scan types to emojis and actions
        type_mapping = {
            "port": {"emoji": "🔍", "action": "scanned"},
            "vulnerability": {"emoji": "🛡️", "action": "analyzed"},
            "score": {"emoji": "🔐", "action": "calculated"},
            "scan": {"emoji": "🚀", "action": "processed"}
        }
        
        config = type_mapping.get(scan_type, {"emoji": "🚀", "action": "processed"})
        
        print(f"{config['emoji']} Progress: {completed}/{total} IPs {config['action']} ({progress_percent:.1f}%) | "
              f"Elapsed: {format_timedelta(elapsed)} | ETA: {format_timedelta(eta)}")

def format_timedelta(td):
    """
    Format timedelta for display
    
    Args:
        td (timedelta): Time delta to format
        
    Returns:
        str: Formatted time string
    """
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def print_scan_summary(completed_scans, failed_scans, total_items_saved, 
                      total_time, save_time=None, total_ips=None, scan_type="scan"):
    """
    Print a summary of the scanning results (generic for both port and vulnerability scans)
    
    Args:
        completed_scans (list): List of completed scan results
        failed_scans (list): List of failed scans
        total_items_saved (int): Total items saved to database
        total_time (timedelta): Total scan time
        save_time (timedelta): Database save time (optional)
        total_ips (int): Total number of IPs that were supposed to be scanned
        scan_type (str): Type of scan for customized messaging
    """
    # Map scan types to emojis and items
    type_mapping = {
        "port": {"emoji": "🔍", "item": "ports"},
        "vulnerability": {"emoji": "🛡️", "item": "vulnerabilities"},
        "score": {"emoji": "🔐", "item": "scores"},
        "scan": {"emoji": "🚀", "item": "items"}
    }
    
    config = type_mapping.get(scan_type, {"emoji": "🚀", "item": "items"})
    total_ips = total_ips or len(completed_scans) + len(failed_scans)
    
    print("\n" + "="*60)
    print(f"{config['emoji']} {scan_type.upper()} SCAN SUMMARY")
    print("="*60)
    
    success_rate = (len(completed_scans) / total_ips) * 100 if total_ips > 0 else 0
    
    print(f"✅ Successfully scanned: {len(completed_scans)}/{total_ips} ({success_rate:.1f}%)")
    print(f"❌ Failed scans: {len(failed_scans)}")
    print(f"💾 {config['item'].title()} saved to database: {total_items_saved}")
    print(f"⏱️  Total time: {format_timedelta(total_time)}")
    
    if save_time:
        print(f"💽 Database save time: {format_timedelta(save_time)}")
    
    if completed_scans:
        avg_time = total_time.total_seconds() / len(completed_scans)
        print(f"📈 Average time per IP: {avg_time:.2f}s")
    
    if failed_scans:
        print(f"\n⚠️  Failed scans ({len(failed_scans)}):")
        for failed in failed_scans[:10]:  # Show first 10 failures
            ip = failed.get('ip_address', failed.get('ip', 'Unknown'))
            print(f"  - {ip}")
        if len(failed_scans) > 10:
            print(f"  ... and {len(failed_scans) - 10} more")
    
    print("="*60) 