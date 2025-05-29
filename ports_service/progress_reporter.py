#!/usr/bin/env python3

from datetime import datetime

def print_progress_update(current, total, start_time, interval=100):
    """
    Print progress update for scanning operations
    
    Args:
        current (int): Current number of completed items
        total (int): Total number of items to process
        start_time (datetime): When the operation started
        interval (int): Print progress every N items
    """
    if current % interval == 0 or current == total:
        elapsed = datetime.now() - start_time
        rate = current / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
        remaining = total - current
        eta_seconds = remaining / rate if rate > 0 else 0
        
        print(f"\n📊 Progress: {current}/{total} ({current/total*100:.1f}%)")
        print(f"⏱️  Elapsed: {elapsed}")
        print(f"🏃 Rate: {rate:.2f} IPs/second")
        print(f"⏰ ETA: {eta_seconds/60:.1f} minutes remaining")

def print_scan_summary(completed_scans, failed_scans, total_ports_saved, total_time, save_time, ip_count):
    """
    Print final summary of scan results
    
    Args:
        completed_scans (list): List of completed scan results
        failed_scans (list): List of failed scans
        total_ports_saved (int): Total number of ports saved to database
        total_time (timedelta): Total time for the operation
        save_time (timedelta): Time spent saving to database
        ip_count (int): Total number of IPs that were supposed to be scanned
    """
    print("\n" + "=" * 60)
    print("🎉 MULTITHREADED SCAN COMPLETE")
    print("=" * 60)
    print(f"✅ Total IPs scanned: {len(completed_scans)}")
    print(f"❌ Failed scans: {len(failed_scans)}")
    print(f"🔓 Total ports saved: {total_ports_saved}")
    print(f"⏱️  Total time: {total_time}")
    print(f"🏃 Average scan rate: {len(completed_scans) / total_time.total_seconds():.2f} IPs/second")

    
    if failed_scans:
        print(f"\n⚠️  Failed scans ({len(failed_scans)}):")
        for failed in failed_scans[:10]:  # Show first 10 failures
            print(f"  - {failed['ip_address']}")
        if len(failed_scans) > 10:
            print(f"  ... and {len(failed_scans) - 10} more")

def print_startup_banner(max_workers=None):
    """
    Print startup banner for the scanning service
    
    Args:
        max_workers (int): Number of threads
    """
    print("🚀 Starting MULTITHREADED port scanning service...")
    print("=" * 60)

def print_ip_retrieval_info(ip_count, limit=None, max_workers=None):
    """
    Print information about IP retrieval and scan configuration
    
    Args:
        ip_count (int): Number of IPs found
        limit (int): Optional limit on number of IPs to scan
        max_workers (int): Number of concurrent threads
    """
    print("📡 Retrieving IP addresses from gossip_peers table...")
    
    if ip_count == 0:
        print("❌ No IP addresses found in database")
        return False
    
    if limit:
        print(f"🔢 Limiting scan to first {limit} IP addresses")
    
    print(f"🎯 Found {ip_count} IP addresses to scan")
    
    if max_workers:
        print(f"🧵 Using {max_workers} concurrent threads")
    
    print("=" * 60)
    
    return True 