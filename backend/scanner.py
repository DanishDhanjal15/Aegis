import scapy.all as scapy
import requests
import socket
import sys
import threading
from database import update_device, clear_devices
from notifications import send_sms_alert

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')

CRITICAL_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 80: "HTTP", 
    443: "HTTPS", 3389: "RDP", 8080: "Alt-HTTP"
}

def get_real_hostname(ip):
    """
    Tries standard Reverse DNS.
    """
    try:
        # Timeout is crucial here to prevent hanging
        socket.setdefaulttimeout(0.5)
        hostname, _, _ = socket.gethostbyaddr(ip)
        if hostname:
            return hostname.replace(".local", "").replace(".lan", "")
    except:
        pass
    return None

def get_mac_vendor(mac):
    try:
        url = f"https://api.macvendors.com/{mac}"
        response = requests.get(url, timeout=1)
        if response.status_code == 200:
            return response.text
    except:
        pass
    return "Unknown Vendor"

def scan_ports(ip):
    open_ports = []
    risk_score = 0
    # Very fast timeout for ports
    for port in CRITICAL_PORTS:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.2) 
        result = s.connect_ex((ip, port))
        if result == 0:
            open_ports.append(port)
            if port == 23: risk_score += 50
            elif port in [21, 3389]: risk_score += 30
            elif port == 80: risk_score += 10
            else: risk_score += 5
        s.close()
    return open_ports, min(risk_score, 100)

def scan_network(target_range=None):
    print("--- STARTING AGGRESSIVE SCAN ---")
    
    # Clear previous scan results
    clear_devices()
    
    # 1. Auto-detect IP
    if not target_range:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            my_ip = s.getsockname()[0]
            s.close()
            ip_parts = my_ip.split('.')
            target_range = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
        except:
            target_range = "192.168.0.1/24"

    try:
        # 2. ARP Discovery (AGGRESSIVE MODE)
        # We send 3 retries and increase timeout to catch sleeping phones
        arp = scapy.ARP(pdst=target_range)
        ether = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether/arp
        
        print(f"📡 Waking up devices on {target_range}...")
        result = scapy.srp(packet, timeout=4, retry=2, verbose=0)[0]
        
        devices = []
        print(f"✅ Found {len(result)} devices. Resolving names...")

        for sent, received in result:
            ip = received.psrc
            mac = received.hwsrc
            
            # Vendor Lookup
            vendor = get_mac_vendor(mac)
            
            # Hostname Lookup
            real_name = get_real_hostname(ip)
            
            # --- NAMING LOGIC ---
            # 1. If we found a real hostname (e.g., "Galaxy-S24"), use it.
            # 2. If no hostname but we know the vendor (e.g., "Apple"), use "Apple Device".
            # 3. If MAC is randomized (common on new phones), it shows "Unknown Vendor".
            #    We rename this to "Private Mobile Device" so it looks better.
            
            if real_name:
                display_name = real_name
                sub_label = vendor
            elif vendor != "Unknown Vendor":
                display_name = vendor
                sub_label = "Generic Device"
            else:
                display_name = "Private Device"
                sub_label = "Randomized MAC (Privacy Mode)"

            # Risk Analysis
            open_ports, port_risk = scan_ports(ip)
            
            device_data = {
                "ip": ip,
                "mac": mac,
                "vendor": display_name,  # The Big Bold Text
                "hostname": sub_label,   # The small text below
                "risk_score": port_risk
            }
            
            update_device(device_data)
            devices.append(device_data)
            
            if port_risk >= 40:
                send_sms_alert(device_data)

        return devices

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return []