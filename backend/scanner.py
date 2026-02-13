import scapy.all as scapy
import requests
import socket
import sys
import threading
from database import update_device, clear_devices, get_all_devices
from notifications import send_sms_alert
from ai_detector import get_ai_detector

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# Vendor cache to avoid repeated API calls
vendor_cache = {}

CRITICAL_PORTS = {
    # File Transfer & Remote Access
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 445: "SMB",
    3389: "RDP", 5900: "VNC", 8080: "Alt-HTTP", 8443: "Alt-HTTPS",
    
    # Database Services
    1433: "MSSQL", 3306: "MySQL", 5432: "PostgreSQL", 6379: "Redis",
    27017: "MongoDB", 9200: "Elasticsearch",
    
    # IoT & Smart Home
    1883: "MQTT", 5683: "CoAP", 8883: "MQTT-SSL", 8123: "Home-Assistant",
    
    # Media & Streaming
    554: "RTSP", 1900: "UPnP", 5000: "UPnP", 8096: "Jellyfin", 32400: "Plex",
    
    # Network Services
    161: "SNMP", 162: "SNMP-Trap", 389: "LDAP", 636: "LDAPS",
    
    # Development & APIs
    3000: "Node.js", 4000: "Dev-Server", 5000: "Flask", 8000: "Django",
    8888: "Jupyter", 9000: "PHP-FPM",
    
    # Security Risks
    135: "RPC", 139: "NetBIOS", 445: "SMB", 512: "Rexec", 513: "Rlogin",
    514: "Rsh", 1080: "SOCKS", 3128: "Squid-Proxy"
}

def get_real_hostname(ip):
    """
    Tries multiple methods to get the actual device name:
    1. Reverse DNS lookup
    2. NetBIOS name query
    3. mDNS/Bonjour query
    """
    hostname = None
    
    # Method 1: Standard Reverse DNS
    try:
        socket.setdefaulttimeout(1.0)
        hostname, _, _ = socket.gethostbyaddr(ip)
        if hostname and hostname != ip:
            # Clean up the hostname
            hostname = hostname.replace(".local", "").replace(".lan", "")
            hostname = hostname.split('.')[0]  # Take first part before domain
            if hostname and len(hostname) > 2:
                return hostname
    except:
        pass
    
    # Method 2: Try NetBIOS name query (Windows devices)
    try:
        import subprocess
        result = subprocess.run(
            ['nbtstat', '-A', ip],
            capture_output=True,
            text=True,
            timeout=2,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if '<00>' in line and 'UNIQUE' in line:
                    # Extract NetBIOS name
                    parts = line.strip().split()
                    if parts and len(parts[0]) > 2:
                        return parts[0]
    except:
        pass
    
    # Method 3: Try mDNS query (Apple devices, some Android)
    try:
        # Send mDNS query
        mdns_query = scapy.IP(dst=ip)/scapy.UDP(dport=5353)/scapy.DNS(
            qd=scapy.DNSQR(qname="_services._dns-sd._udp.local", qtype="PTR")
        )
        ans = scapy.sr1(mdns_query, timeout=1, verbose=0)
        if ans and ans.haslayer(scapy.DNS):
            # Try to extract hostname from mDNS response
            if hasattr(ans[scapy.DNS], 'an') and ans[scapy.DNS].an:
                name = str(ans[scapy.DNS].an.rrname)
                if name and '.local' in name:
                    return name.replace('.local', '').replace('._tcp', '').replace('._udp', '')
    except:
        pass
    
    return None

def get_mac_vendor(mac):
    # Check cache first
    if mac in vendor_cache:
        return vendor_cache[mac]
    
    try:
        url = f"https://api.macvendors.com/{mac}"
        response = requests.get(url, timeout=0.3)
        if response.status_code == 200:
            vendor = response.text.strip()
            vendor_cache[mac] = vendor
            return vendor
    except:
        pass
    
    vendor_cache[mac] = "Unknown Vendor"
    return "Unknown Vendor"

def detect_os(ip):
    """
    Attempts to detect OS based on TTL values from ping response.
    """
    try:
        # Send ICMP ping
        ans = scapy.sr1(scapy.IP(dst=ip)/scapy.ICMP(), timeout=1, verbose=0)
        if ans:
            ttl = ans.ttl
            # Common TTL values:
            # Windows: 128, Linux: 64, Cisco: 255, macOS: 64
            if ttl <= 64:
                return "Linux/Unix/macOS"
            elif ttl <= 128:
                return "Windows"
            elif ttl <= 255:
                return "Network Device"
    except:
        pass
    return "Unknown"

def classify_device_type(vendor, open_ports):
    """
    Classifies device type based on vendor and open ports.
    """
    vendor_lower = vendor.lower()
    
    # Router/Network Equipment
    if any(x in vendor_lower for x in ['cisco', 'netgear', 'tp-link', 'linksys', 'asus router', 'd-link']):
        return "router"
    
    # Mobile Devices
    if any(x in vendor_lower for x in ['apple', 'samsung', 'xiaomi', 'huawei', 'oneplus', 'google']):
        if any(x in vendor_lower for x in ['iphone', 'ipad', 'galaxy', 'pixel']):
            return "mobile"
    
    # Smart Home / IoT
    if any(x in vendor_lower for x in ['philips hue', 'nest', 'ring', 'ecobee', 'sonos', 'amazon', 'google home']):
        return "iot"
    if 1883 in open_ports or 8123 in open_ports:  # MQTT or Home Assistant
        return "iot"
    
    # Media Devices
    if 32400 in open_ports or 8096 in open_ports:  # Plex or Jellyfin
        return "media"
    if any(x in vendor_lower for x in ['roku', 'chromecast', 'apple tv', 'fire tv']):
        return "media"
    
    # Servers
    if any(port in open_ports for port in [3306, 5432, 27017, 1433, 6379]):  # Database ports
        return "server"
    if any(port in open_ports for port in [22, 3389, 5900]):  # Remote access
        return "server"
    
    # Laptops/Desktops
    if any(x in vendor_lower for x in ['dell', 'hp', 'lenovo', 'asus', 'acer', 'msi']):
        return "laptop"
    
    return "unknown"

def measure_latency(ip):
    """
    Measures network latency to device in milliseconds.
    """
    try:
        import time
        start = time.time()
        ans = scapy.sr1(scapy.IP(dst=ip)/scapy.ICMP(), timeout=2, verbose=0)
        if ans:
            latency = (time.time() - start) * 1000  # Convert to ms
            return round(latency, 2)
    except:
        pass
    return None

def scan_ports(ip):
    open_ports = []
    risk_score = 0
    # Ultra-fast timeout for ports
    for port in CRITICAL_PORTS:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.15)  # Slightly increased for more ports
            result = s.connect_ex((ip, port))
            if result == 0:
                open_ports.append(port)
                # Risk scoring based on severity
                if port in [23, 512, 513, 514]:  # Legacy/dangerous protocols
                    risk_score += 50
                elif port in [21, 3389, 5900, 135, 139, 445]:  # High-risk remote access
                    risk_score += 30
                elif port in [3306, 5432, 27017, 1433, 6379, 9200]:  # Exposed databases
                    risk_score += 25
                elif port in [80, 8080, 8000]:  # Unencrypted web
                    risk_score += 10
                elif port in [1883, 161]:  # IoT/SNMP
                    risk_score += 15
                else:
                    risk_score += 5
            s.close()
        except:
            pass
    return open_ports, min(risk_score, 100)

def scan_network(target_range=None):
    print("--- STARTING FRESH NETWORK SCAN ---")
    
    # 1. Auto-detect IP
    if not target_range:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            my_ip = s.getsockname()[0]
            s.close()
            ip_parts = my_ip.split('.')
            target_range = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
            print(f"📡 Detected network: {target_range}")
        except:
            target_range = "192.168.0.1/24"
            print(f"⚠️ Using default range: {target_range}")

    try:
        # Perform ARP scan to discover ALL devices currently on the network
        arp = scapy.ARP(pdst=target_range)
        ether = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether/arp
        
        print(f"🔍 Scanning for active devices on {target_range}...")
        
        # Increased timeout for better device discovery
        # Suppress Scapy warnings about broadcast MAC address
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                answered, unanswered = scapy.srp(packet, timeout=3, retry=2, verbose=0)
                result = answered
            except Exception as e:
                print(f"❌ ARP scan error: {e}")
                print(f"⚠️ Returning previously cached devices")
                return get_all_devices()
        
        if not result:
            print(f"⚠️ No devices found in ARP scan")
            # Return cached devices if scan fails
            cached = get_all_devices()
            if cached:
                print(f"📦 Returning {len(cached)} cached devices")
            return cached
        
        devices = []
        print(f"✅ Found {len(result)} devices. Processing...")

        for idx, (sent, received) in enumerate(result):
            # Extract basic info first (should always work)
            try:
                ip = received.psrc
                mac = received.hwsrc
                
                # Validate MAC address format
                if not mac or len(mac) < 12 or not isinstance(mac, str):
                    print(f"   ⚠ [{idx+1}/{len(result)}] Invalid MAC address for {ip}: {mac}")
                    mac = f"00:00:00:00:00:{idx:02x}"  # Fallback MAC
                    print(f"      Using fallback MAC: {mac}")
                
                # Validate IP address
                if not ip or not isinstance(ip, str) or len(ip.split('.')) != 4:
                    print(f"   ⚠ [{idx+1}/{len(result)}] Invalid IP address: {ip}")
                    continue
                    
            except Exception as e:
                print(f"   ✗ [{idx+1}/{len(result)}] Failed to extract IP/MAC: {e}")
                import traceback
                traceback.print_exc()
                continue
            
            # Initialize device data with defaults - we'll enrich it step by step
            device_data = {
                "ip": ip,
                "mac": mac,
                "vendor": "Unknown Vendor",
                "hostname": "Unknown",
                "risk_score": 0,
                "os_type": "Unknown",
                "device_type": "unknown",
                "open_ports": 0,
                "port_summary": "No open ports",
                "latency": None
            }
            
            # Try each enrichment step individually - if one fails, continue with defaults
            try:
                vendor = get_mac_vendor(mac)
                device_data["vendor"] = vendor if vendor else "Unknown Vendor"
            except Exception as e:
                print(f"   ⚠ [{idx+1}/{len(result)}] Vendor lookup failed for {ip}: {e}")
            
            try:
                real_hostname = get_real_hostname(ip)
                if real_hostname:
                    device_data["hostname"] = real_hostname
            except Exception as e:
                # Hostname lookup is optional, fail silently
                pass
            
            try:
                # Try AI-powered OS detection first
                ai_detector = get_ai_detector()
                os_type_ai = ai_detector.detect_os_ai(device_data)
                
                # Fallback to traditional detection if AI returns Unknown
                if os_type_ai == "Unknown" or not os_type_ai:
                    os_type = detect_os(ip)
                    device_data["os_type"] = os_type if os_type else "Unknown"
                else:
                    device_data["os_type"] = os_type_ai
            except Exception as e:
                # Fallback to traditional OS detection
                try:
                    os_type = detect_os(ip)
                    device_data["os_type"] = os_type if os_type else "Unknown"
                except:
                    device_data["os_type"] = "Unknown"
            
            open_ports = []
            try:
                open_ports, port_risk = scan_ports(ip)
                device_data["open_ports"] = open_ports  # Store list for AI detector
                device_data["open_ports_count"] = len(open_ports)
                device_data["risk_score"] = port_risk
                
                # Create port summary
                port_names = [CRITICAL_PORTS.get(p, str(p)) for p in open_ports[:5]]
                device_data["port_summary"] = ", ".join(port_names) if port_names else "No open ports"
            except Exception as e:
                print(f"   ⚠ [{idx+1}/{len(result)}] Port scan failed for {ip}: {e}")
                device_data["open_ports"] = []
                device_data["open_ports_count"] = 0
            
            try:
                # Use AI-powered device type classification
                ai_detector = get_ai_detector()
                device_type_ai = ai_detector.classify_device_type_ai(device_data)
                
                # Fallback to traditional classification if AI returns unknown
                if device_type_ai == "unknown" or not device_type_ai:
                    device_type = classify_device_type(device_data["vendor"], open_ports)
                    device_data["device_type"] = device_type
                else:
                    device_data["device_type"] = device_type_ai
            except Exception as e:
                # Fallback to traditional classification
                try:
                    device_type = classify_device_type(device_data["vendor"], open_ports)
                    device_data["device_type"] = device_type
                except:
                    device_data["device_type"] = "unknown"
            
            try:
                latency = measure_latency(ip)
                if latency:
                    device_data["latency"] = latency
            except Exception as e:
                # Latency measurement is optional
                pass
            
            # Store TTL for AI detection
            try:
                ans = scapy.sr1(scapy.IP(dst=ip)/scapy.ICMP(), timeout=1, verbose=0)
                if ans:
                    device_data["ttl"] = ans.ttl
            except:
                device_data["ttl"] = 64  # Default
            
            # --- AI-POWERED INTELLIGENT NAMING ---
            try:
                ai_detector = get_ai_detector()
                display_name, sub_label = ai_detector.generate_intelligent_name(device_data)
                
                device_data["original_vendor"] = device_data.get("vendor", "Unknown Vendor")
                device_data["display_name"] = display_name
                device_data["sub_label"] = sub_label
                
                # Add to training data for future model improvement
                ai_detector.add_training_sample(device_data.copy())
            except Exception as e:
                # Fallback to traditional naming if AI fails
                real_hostname = device_data.get("hostname") if device_data.get("hostname") != "Unknown" else None
                vendor = device_data.get("vendor")
                os_type = device_data.get("os_type")
                
                if real_hostname:
                    display_name = real_hostname
                    sub_label = vendor if vendor != "Unknown Vendor" else (os_type if os_type != "Unknown" else "Device")
                elif vendor != "Unknown Vendor":
                    display_name = vendor
                    sub_label = os_type if os_type != "Unknown" else "Device"
                else:
                    display_name = f"Device-{ip.split('.')[-1]}"
                    sub_label = os_type if os_type != "Unknown" else "Randomized MAC"
                
                device_data["display_name"] = display_name
                device_data["sub_label"] = sub_label
            
            # Always save the device, even if enrichment partially failed
            try:
                success = update_device(device_data)
                if success:
                    devices.append(device_data)
                    
                # Enhanced logging
                latency_str = f"{device_data['latency']}ms" if device_data['latency'] else "N/A"
                port_count = device_data.get('open_ports_count', device_data.get('open_ports', 0))
                if isinstance(port_count, list):
                    port_count = len(port_count)
                print(f"   ✓ [{idx+1}/{len(result)}] {display_name} ({ip}) | {device_data.get('os_type', 'Unknown')} | {port_count} ports | {latency_str}")
                
                if device_data["risk_score"] >= 40:
                    try:
                        send_sms_alert(device_data)
                    except Exception as e:
                        print(f"   ⚠ SMS alert failed for {ip}: {e}")
                else:
                    print(f"   ✗ [{idx+1}/{len(result)}] Database save failed for {ip} ({mac})")
            except Exception as e:
                print(f"   ✗ [{idx+1}/{len(result)}] Exception saving device {ip} ({mac}): {e}")
                import traceback
                traceback.print_exc()

        print(f"✅ SCAN COMPLETE: {len(devices)}/{len(result)} devices saved to database.")
        if len(devices) < len(result):
            print(f"   ⚠ {len(result) - len(devices)} devices failed to save - check errors above")
        return devices

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return get_all_devices()  # Return cached devices on error
