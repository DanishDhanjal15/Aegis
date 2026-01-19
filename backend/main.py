from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import urllib.parse
import time
import threading
from scanner import scan_network
from database import get_all_devices

# --- IMPORT OUR MODULES ---
from scanner import scan_network
from database import (
    init_db, 
    get_all_devices, 
    get_recent_logs, 
    toggle_block_status
)
from blocker import start_blocking, stop_blocking

# Initialize App
app = FastAPI(title="Aegis IoT Guardian")

# Enable CORS (Allows Frontend to talk to Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- STARTUP EVENT ---
@app.on_event("startup")
def startup_event():
    """Initialize the database when the server starts."""
    init_db()

# --- HOME ROUTE ---
@app.get("/")
def home():
    return {"status": "Aegis System Online", "version": "2.0 (Real-Blocking Enabled)"}

# --- DEVICE ENDPOINTS ---
@app.get("/api/devices")
def read_devices():
    """Returns the list of all devices from the database."""
    return get_all_devices()

@app.post("/api/panic")
def trigger_panic():
    """Triggers a panic mode that blocks all devices."""
    all_devices = get_all_devices()
    for device in all_devices:
        decoded_mac = urllib.parse.unquote(device['mac'])
        new_status = toggle_block_status(decoded_mac)
        target_device = next((d for d in all_devices if d['mac'] == decoded_mac), None)
        decoded_mac = urllib.parse.unquote(device['mac'])
        if target_device:
            target_ip = target_device['ip']
            
            # 4. Trigger Real Network Block
            if new_status == 1: # Status 1 = BLOCKED
                print(f"🚫 ACTIVATING BLOCKER for {target_ip} ({decoded_mac})")
                start_blocking(target_ip)
            else: # Status 0 = UNBLOCKED
                print(f"✅ DEACTIVATING BLOCKER for {target_ip}")
                stop_blocking(target_ip)
        else:
            print("Warning: Device found in DB but could not resolve IP for blocking.")
                
        return {"status": "success", "isBlocked": bool(new_status)}

@app.post("/api/scan")
def trigger_scan():
    """Triggers a real network scan and updates the DB."""
    devices = scan_network() 
    return {"message": "Scan Complete", "devices_found": len(devices)}

# --- BLOCK ENDPOINT (THE KEY FEATURE) ---
@app.post("/api/device/{mac}/block")
def block_device_endpoint(mac: str):
    """
    Toggles the block status of a device.
    1. Updates Database.
    2. Starts/Stops the physical ARP Spoofing thread.
    """
    # 1. Decode MAC (Frontend sends encoded URL chars like %3A)
    decoded_mac = urllib.parse.unquote(mac)
    
    # 2. Update Status in SQLite Database
    new_status = toggle_block_status(decoded_mac)
    
    if new_status is None:
        raise HTTPException(status_code=404, detail="Device not found in database")
        
    # 3. Find the Device's IP to target the Attack
    all_devices = get_all_devices()
    target_device = next((d for d in all_devices if d['mac'] == decoded_mac), None)
    
    if target_device:
        target_ip = target_device['ip']
        
        # 4. Trigger Real Network Block
        if new_status == 1: # Status 1 = BLOCKED
            print(f"🚫 ACTIVATING BLOCKER for {target_ip} ({decoded_mac})")
            start_blocking(target_ip)
        else: # Status 0 = UNBLOCKED
            print(f"✅ DEACTIVATING BLOCKER for {target_ip}")
            stop_blocking(target_ip)
    else:
        print("Warning: Device found in DB but could not resolve IP for blocking.")
            
    return {"status": "success", "isBlocked": bool(new_status)}

# --- LOGS ENDPOINT ---
@app.get("/api/logs")
def read_logs():
    """Returns recent activity logs."""
    return get_recent_logs()

if __name__ == "__main__":
    # Host 0.0.0.0 is crucial so other devices on the network can potentially be managed
    # Port 8000 is standard
    print("🚀 Aegis Server Starting...")
    print("⚠️  Ensure you are running as Administrator/Root for Blocking to work!")
    uvicorn.run(app, host="0.0.0.0", port=8000)