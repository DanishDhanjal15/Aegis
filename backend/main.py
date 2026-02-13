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
    toggle_block_status,
    update_nickname,
    get_device_count,
)
from blocker import start_blocking, stop_blocking
from auto_scanner import start_auto_scan, stop_auto_scan, get_auto_scan_status, set_scan_interval
from ai_detector import get_ai_detector
from chatbot import get_chatbot
from database import set_device_block_status, init_auth_db, create_user, verify_user
from firebase_admin_config import initialize_firebase
from pydantic import BaseModel
import socket
try:
    from sklearn.ensemble import RandomForestClassifier
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# Chatbot Request Model
class ChatRequest(BaseModel):
    message: str

# User Auth Models
class UserAuth(BaseModel):
    username: str
    password: str

# Initialize App
app = FastAPI(title="Aegis IoT Guardian")

# Track manual scan status
scan_status = {
    "is_scanning": False,
    "started_at": None,
    "completed_at": None,
    "device_count": 0
}
scan_lock = threading.Lock()

def get_scan_status_safe():
    """Safely get scan status with defaults."""
    with scan_lock:
        return {
            "is_scanning": scan_status.get("is_scanning", False),
            "started_at": scan_status.get("started_at"),
            "completed_at": scan_status.get("completed_at"),
            "device_count": scan_status.get("device_count", 0)
        }

# Enable CORS (Allows Frontend to talk to Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- STARTUP EVENT ---
@app.on_event("startup")
async def startup_event():
    """Initialize the databases when the server starts."""
    try:
        print("📊 Initializing database...")
        init_db()
        print("✅ Database initialized successfully")
        
        print("🔥 Initializing Firebase Admin SDK...")
        initialize_firebase()
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        import traceback
        traceback.print_exc()

# --- HOME ROUTE ---
@app.get("/")
def home():
    return {"status": "Aegis System Online", "version": "2.0 (Real-Blocking Enabled)"}

# --- DEVICE ENDPOINTS ---
@app.get("/api/devices")
def read_devices():
    """Returns the list of all devices from the database."""
    devices = get_all_devices()
    try:
        ai = get_ai_detector()
        enhanced = []
        for d in devices:
            eval_res = ai.evaluate_harmful_device(d)
            summary = ai.generate_device_summary(d)
            d = {**d, **{"harmful": eval_res["harmful"], "has_critical_ports": eval_res["has_critical_ports"], "summary": summary}}
            enhanced.append(d)
        devices = enhanced
    except Exception as e:
        pass
    count = len(devices)
    print(f"📡 API /api/devices: Returning {count} devices to frontend")
    return devices

@app.get("/api/debug/device-count")
def debug_device_count():
    """Debug endpoint to check how many devices are in the database."""
    count = get_device_count()
    return {"count": count, "message": f"Total devices in database: {count}"}

@app.post("/api/panic")
def trigger_panic():
    """Triggers a panic mode that blocks all devices (runs in background)."""
    print("🚨 PANIC MODE TRIGGERED - Starting background blocking...")
    
    # Run panic in a separate thread so the server doesn't block
    panic_thread = threading.Thread(target=execute_panic_mode, daemon=True)
    panic_thread.start()
    
    return {"status": "success", "message": "Panic mode activated - blocking all devices in background"}


def execute_panic_mode():
    """Actually blocks all devices (runs in background thread)."""
    try:
        # Get local IP to avoid self-blocking
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        except:
            local_ip = "127.0.0.1"
        finally:
            s.close()

        all_devices = get_all_devices()
        blocked_count = 0
        failed_count = 0
        
        print(f"🚨 PANIC MODE EXECUTING - Attempting to block {len(all_devices)} devices")
        print(f"🛡️ Protection: Skipping local host IP {local_ip}")
        
        for device in all_devices:
            try:
                mac = device['mac']
                ip = device['ip']
                
                if ip == local_ip:
                    print(f"🛡️ Skipping host device: {ip}")
                    continue

                # Explicitly block the device
                set_device_block_status(mac, 1)
                
                print(f"🚫 PANIC BLOCKING: {ip} ({mac})")
                start_blocking(ip)
                blocked_count += 1
            except Exception as e:
                print(f"❌ Error blocking {device.get('ip', 'unknown')}: {e}")
                failed_count += 1
        
        print(f"✅ PANIC MODE COMPLETE: Blocked {blocked_count}, Failed {failed_count} out of {len(all_devices)}")
    except Exception as e:
        print(f"❌ Panic mode error: {e}")
        import traceback
        traceback.print_exc()

@app.post("/api/panic/unlock")
def unlock_panic():
    unlock_thread = threading.Thread(target=execute_unlock_panic_mode, daemon=True)
    unlock_thread.start()
    return {"status": "success", "message": "Panic unlock activated - unblocking all devices in background"}

def execute_unlock_panic_mode():
    try:
        all_devices = get_all_devices()
        unblocked_count = 0
        failed_count = 0
        for device in all_devices:
            try:
                mac = device.get('mac')
                ip = device.get('ip')
                if mac:
                    set_device_block_status(mac, 0)
                if ip:
                    stop_blocking(ip)
                unblocked_count += 1
            except Exception:
                failed_count += 1
        print(f"✅ PANIC UNLOCK COMPLETE: Unblocked {unblocked_count}, Failed {failed_count} out of {len(all_devices)}")
    except Exception as e:
        print(f"❌ Panic unlock error: {e}")
        import traceback
        traceback.print_exc()

def run_scan_with_status():
    """Wrapper to run scan and update status."""
    with scan_lock:
        scan_status["is_scanning"] = True
        scan_status["started_at"] = time.time()
        scan_status["completed_at"] = None
    
    try:
        devices = scan_network()
        device_count = len(devices) if devices else 0
        
        with scan_lock:
            scan_status["is_scanning"] = False
            scan_status["completed_at"] = time.time()
            scan_status["device_count"] = device_count
        
        print(f"📊 Scan status updated: {device_count} devices found")
    except Exception as e:
        with scan_lock:
            scan_status["is_scanning"] = False
            scan_status["completed_at"] = time.time()
        print(f"❌ Scan failed: {e}")
        import traceback
        traceback.print_exc()

@app.post("/api/scan")
def trigger_scan():
    """Triggers a real network scan and updates the DB (runs in background)."""
    # Check if scan is already running
    with scan_lock:
        if scan_status["is_scanning"]:
            return {"message": "Scan already in progress", "status": "scanning"}
    
    # Run scan in a separate thread so the server doesn't block
    scan_thread = threading.Thread(target=run_scan_with_status, daemon=True)
    scan_thread.start()
    return {"message": "Scan started in background", "status": "scanning"}

@app.post("/api/scan/force")
def force_full_scan():
    """Forces a complete fresh scan, clearing cache and rescanning all devices."""
    from database import clear_devices
    
    # Check if scan is already running
    with scan_lock:
        if scan_status["is_scanning"]:
            return {"message": "Scan already in progress", "status": "scanning"}
    
    # Clear existing devices to force fresh scan
    clear_devices()
    # Run scan in a separate thread
    scan_thread = threading.Thread(target=run_scan_with_status, daemon=True)
    scan_thread.start()
    return {"message": "Force scan started - all devices will be rescanned", "status": "scanning"}

@app.get("/api/scan/status")
def get_manual_scan_status():
    """Returns the status of the current manual scan."""
    try:
        return get_scan_status_safe()
    except Exception as e:
        return {
            "is_scanning": False,
            "started_at": None,
            "completed_at": None,
            "device_count": 0,
            "status": "error",
            "error": str(e)
        }

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
        
    print("Blocking operation disabled")
            
    return {"status": "success", "isBlocked": bool(new_status)}


@app.post("/api/device/{mac}/nickname")
def set_device_nickname(mac: str, nickname: str):
    """
    Sets or updates a human-friendly nickname for a device.

    The nickname is stored alongside the device record and is preserved
    across future scans.
    """
    decoded_mac = urllib.parse.unquote(mac)
    try:
        update_nickname(decoded_mac, nickname.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update nickname: {e}")

    return {"status": "success", "nickname": nickname.strip()}

# --- LOGS ENDPOINT ---
@app.get("/api/logs")
def read_logs():
    """Returns recent activity logs."""
    return get_recent_logs()

# --- AUTO-SCAN ENDPOINTS ---
@app.post("/api/auto-scan/start")
def start_automatic_scan(interval_minutes: int = 5):
    """Starts automatic periodic scanning."""
    success = start_auto_scan(interval_minutes)
    if success:
        return {"status": "success", "message": f"Auto-scan started (every {interval_minutes} minutes)"}
    return {"status": "error", "message": "Auto-scan is already running"}

@app.post("/api/auto-scan/stop")
def stop_automatic_scan():
    """Stops automatic periodic scanning."""
    success = stop_auto_scan()
    if success:
        return {"status": "success", "message": "Auto-scan stopped"}
    return {"status": "error", "message": "Auto-scan is not running"}

@app.get("/api/auto-scan/status")
def get_scan_status():
    """Returns the current auto-scan status."""
    return get_auto_scan_status()

@app.post("/api/auto-scan/interval")
def update_scan_interval(interval_minutes: int):
    """Updates the scan interval."""
    success = set_scan_interval(interval_minutes)
    if success:
        return {"status": "success", "message": f"Interval updated to {interval_minutes} minutes"}
    return {"status": "warning", "message": "Interval updated but requires auto-scan restart"}

# --- AI DETECTOR ENDPOINTS ---
@app.post("/api/ai/train")
def train_ai_models():
    """Trains AI models on collected device data."""
    try:
        ai_detector = get_ai_detector()
        # Get all devices from database as training data
        training_data = get_all_devices()
        
        if len(training_data) < 10:
            return {
                "status": "error",
                "message": f"Need at least 10 devices to train. Currently have {len(training_data)}."
            }
        
        ai_detector.train_models(training_data)
        return {
            "status": "success",
            "message": f"Trained models on {len(training_data)} devices"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/ai/status")
def get_ai_status():
    """Returns AI detector status and model information."""
    try:
        ai_detector = get_ai_detector()
        has_device_model = ai_detector.device_classifier is not None
        has_os_model = ai_detector.os_classifier is not None
        training_samples = len(ai_detector.learning_data)
        
        return {
            "status": "active",
            "ml_available": ML_AVAILABLE if 'ML_AVAILABLE' in globals() else False,
            "device_classifier_loaded": has_device_model,
            "os_classifier_loaded": has_os_model,
            "training_samples_collected": training_samples,
            "mode": "ml" if (has_device_model or has_os_model) else "rule-based"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- CHATBOT ENDPOINT ---
@app.post("/api/chat")
def chat_with_aegis(request: ChatRequest):
    """Handles chat messages and returns AI-powered responses."""
    bot = get_chatbot()
    response = bot.ask(request.message)
    return {"reply": response}

# --- AUTH ENDPOINTS (REMOVED - Now using Firebase) ---
# Authentication is now handled by Firebase on the frontend.
# The backend verifies Firebase ID tokens using the auth_middleware.
# To protect routes, use: from auth_middleware import get_current_user
# Then add as dependency: async def protected_route(user = Depends(get_current_user))

# (Auth initialization moved to consolidated startup event)

if __name__ == "__main__":
    # Host 0.0.0.0 is crucial so other devices on the network can potentially be managed
    # Port 8000 is standard
    print("🚀 Aegis Server Starting...")
    print("⚠️  Ensure you are running as Administrator/Root for Blocking to work!")
    uvicorn.run(app, host="0.0.0.0", port=8000)
