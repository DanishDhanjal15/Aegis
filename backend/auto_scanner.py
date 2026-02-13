import threading
import time
from scanner import scan_network
from database import add_log

# Configuration
SCAN_INTERVAL_MINUTES = 5  # Default: scan every 5 minutes
auto_scan_enabled = False
auto_scan_thread = None

def auto_scan_loop():
    """
    Background thread that runs periodic network scans.
    """
    global auto_scan_enabled
    
    while auto_scan_enabled:
        try:
            print(f"🔄 AUTO-SCAN: Starting scheduled scan...")
            add_log("Automatic network scan initiated", "info")
            
            # Run the scan
            devices = scan_network()
            
            print(f"✅ AUTO-SCAN: Completed. Found {len(devices)} devices.")
            add_log(f"Auto-scan completed: {len(devices)} devices found", "success")
            
        except Exception as e:
            print(f"❌ AUTO-SCAN ERROR: {e}")
            add_log(f"Auto-scan failed: {str(e)}", "danger")
        
        # Wait for the configured interval
        for _ in range(SCAN_INTERVAL_MINUTES * 60):
            if not auto_scan_enabled:
                break
            time.sleep(1)
    
    print("🛑 AUTO-SCAN: Stopped")

def start_auto_scan(interval_minutes=5):
    """
    Starts automatic periodic scanning.
    """
    global auto_scan_enabled, auto_scan_thread, SCAN_INTERVAL_MINUTES
    
    if auto_scan_enabled:
        print("⚠️ Auto-scan is already running")
        return False
    
    SCAN_INTERVAL_MINUTES = interval_minutes
    auto_scan_enabled = True
    
    auto_scan_thread = threading.Thread(target=auto_scan_loop, daemon=True)
    auto_scan_thread.start()
    
    print(f"✅ AUTO-SCAN: Started (interval: {interval_minutes} minutes)")
    add_log(f"Automatic scanning enabled (every {interval_minutes} min)", "info")
    return True

def stop_auto_scan():
    """
    Stops automatic periodic scanning.
    """
    global auto_scan_enabled
    
    if not auto_scan_enabled:
        print("⚠️ Auto-scan is not running")
        return False
    
    auto_scan_enabled = False
    print("🛑 AUTO-SCAN: Stopping...")
    add_log("Automatic scanning disabled", "warning")
    return True

def get_auto_scan_status():
    """
    Returns the current auto-scan status.
    """
    return {
        "enabled": auto_scan_enabled,
        "interval_minutes": SCAN_INTERVAL_MINUTES
    }

def set_scan_interval(minutes):
    """
    Updates the scan interval (requires restart if already running).
    """
    global SCAN_INTERVAL_MINUTES
    SCAN_INTERVAL_MINUTES = minutes
    
    if auto_scan_enabled:
        print(f"⚠️ Interval updated to {minutes} minutes. Restart auto-scan for changes to take effect.")
        return False
    return True
