import os
import sqlite3
from datetime import datetime

# Build absolute path to database file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "aegis.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Table for Devices - Enhanced Schema
    c.execute('''CREATE TABLE IF NOT EXISTS devices 
                 (mac TEXT PRIMARY KEY, ip TEXT, vendor TEXT, 
                  hostname TEXT, risk_score INTEGER, status TEXT, last_seen TEXT,
                  os_type TEXT, device_type TEXT, open_ports INTEGER,
                  port_summary TEXT, latency REAL, nickname TEXT, is_blocked INTEGER DEFAULT 0)''')
    
    # Table for Users - NEW
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, created_at TEXT)''')
    
    conn.commit()
    conn.close()

def update_device(device):
    """
    Saves or updates a device in the database.
    Validates required fields and handles errors gracefully.
    """
    # Validate required fields
    if not device.get('mac') or not device.get('ip'):
        print(f"⚠️ Skipping device with missing MAC or IP: {device}")
        return False
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    try:
        # Preserve any existing nickname for this MAC address unless explicitly overridden.
        nickname = device.get("nickname")
        try:
            c.execute("SELECT nickname FROM devices WHERE mac=?", (device["mac"],))
            row = c.fetchone()
            if row is not None and row[0] is not None and nickname is None:
                nickname = row[0]
        except sqlite3.OperationalError:
            pass
        
        # Ensure all required fields have defaults
        mac = str(device['mac']).strip()
        ip = str(device['ip']).strip()
        vendor = str(device.get('vendor', 'Unknown Vendor'))[:200]
        hostname = str(device.get('hostname', 'Unknown'))[:200]
        risk_score = int(device.get('risk_score', 0))
        os_type = str(device.get('os_type', 'Unknown'))[:100]
        device_type = str(device.get('device_type', 'unknown'))[:50]
        
        open_ports_raw = device.get('open_ports', 0)
        if isinstance(open_ports_raw, list):
            open_ports = len(open_ports_raw)
        else:
            open_ports = int(open_ports_raw)
        
        port_summary = str(device.get('port_summary', ''))[:500]
        latency = device.get('latency')
        if latency is not None:
            try:
                latency = float(latency)
            except (ValueError, TypeError):
                latency = None
        
        # Check if device already exists
        c.execute("SELECT mac FROM devices WHERE mac=?", (mac,))
        exists = c.fetchone() is not None
        
        c.execute('''INSERT OR REPLACE INTO devices 
                     (mac, ip, vendor, hostname, risk_score, status, last_seen,
                      os_type, device_type, open_ports, port_summary, latency, nickname)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                     (mac, ip, vendor, hostname, risk_score, 'Online', datetime.now().isoformat(),
                      os_type, device_type, open_ports, port_summary, latency, nickname))
        conn.commit()
        
        action = "Updated" if exists else "Added"
        print(f"   💾 {action} device: {mac} ({ip}) - {vendor[:30]}")
        return True
    except Exception as e:
        print(f"❌ Database error saving device: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_all_devices():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM devices ORDER BY last_seen DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_device_count():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM devices")
    count = c.fetchone()[0]
    conn.close()
    return count

def add_log(event, log_type="info"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT, event TEXT, type TEXT)''')
    time_str = datetime.now().strftime("%I:%M %p")
    c.execute("INSERT INTO logs (time, event, type) VALUES (?, ?, ?)", (time_str, event, log_type))
    conn.commit()
    conn.close()

def get_recent_logs():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 50")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def clear_devices():
    """Deletes all devices from the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM devices")
    conn.commit()
    conn.close()

def update_nickname(mac, nickname):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE devices SET nickname=? WHERE mac=?", (nickname, mac))
    if c.rowcount:
        add_log(f"Label set for device {mac}: \"{nickname}\"", "info")
    conn.commit()
    conn.close()

def toggle_block_status(mac):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT is_blocked, vendor FROM devices WHERE mac=?", (mac,))
    row = c.fetchone()
    if not row:
        conn.close()
        return None
    new_status = 0 if row[0] == 1 else 1
    c.execute("UPDATE devices SET is_blocked=? WHERE mac=?", (new_status, mac))
    conn.commit()
    conn.close()
    status_str = "Blocked" if new_status else "Unblocked"
    add_log(f"Manual Override: {status_str} device {row[1]}", "warning" if new_status else "success")
    return new_status

def set_device_block_status(mac, status):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT vendor FROM devices WHERE mac=?", (mac,))
    row = c.fetchone()
    vendor = row[0] if row else "Unknown"
    c.execute("UPDATE devices SET is_blocked=? WHERE mac=?", (status, mac))
    conn.commit()
    conn.close()
    status_str = "Blocked" if status else "Unblocked"
    add_log(f"System Action: {status_str} device {vendor}", "error" if status else "success")
    return status

# --- AUTH FUNCTIONS ---

def init_auth_db():
    """Initializes the users table for authentication."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, created_at TEXT)''')
    conn.commit()
    conn.close()

def create_user(username, password):
    """Creates a new user in the database."""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)",
                  (username, password, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def verify_user(username, password):
    """Verifies user credentials."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row and row[0] == password:
        return True
    return False