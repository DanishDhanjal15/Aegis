import sqlite3
from datetime import datetime

DB_NAME = "aegis.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Table for Devices
    c.execute('''CREATE TABLE IF NOT EXISTS devices 
                 (mac TEXT PRIMARY KEY, ip TEXT, vendor TEXT, 
                  hostname TEXT, risk_score INTEGER, status TEXT, last_seen TEXT)''')
    conn.commit()
    conn.close()

def update_device(device):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO devices (mac, ip, vendor, hostname, risk_score, status, last_seen)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                 (device['mac'], device['ip'], device['vendor'], device['hostname'], 
                  device['risk_score'], 'Online', datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_all_devices():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM devices")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_log(event, log_type="info"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Create logs table if it doesn't exist
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
    # Create table just in case
    c.execute('''CREATE TABLE IF NOT EXISTS logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT, event TEXT, type TEXT)''')
    c.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 50")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def clear_devices():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM devices")
    conn.commit()
    conn.close()

def toggle_block_status(mac):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Ensure column exists (migration for existing db)
    try:
        c.execute("SELECT is_blocked FROM devices LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE devices ADD COLUMN is_blocked INTEGER DEFAULT 0")
        conn.commit()

    # Get current status
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