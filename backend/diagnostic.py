import scapy.all as scapy
import socket

def test_connectivity():
    print("--- STEP 1: NETWORK INFO ---")
    # 1. Get local IP
    s = socket.socket(socket.socket.AF_INET, socket.socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        my_ip = s.getsockname()[0]
        s.close()
        print(f"✅ Your Local IP is: {my_ip}")
        
        # Calculate range
        ip_parts = my_ip.split('.')
        target_range = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
        print(f"🎯 Target Scan Range: {target_range}")
        return target_range
    except Exception as e:
        print(f"❌ Could not determine IP: {e}")
        return None

def list_interfaces():
    print("\n--- STEP 2: AVAILABLE INTERFACES ---")
    # Show all interfaces Scapy can see
    ifaces = scapy.get_if_list()
    for i in ifaces:
        print(f" - {i}")
    
    # Try to find the one with our IP
    print("\nAttempting to match interface...")
    conf_iface = scapy.conf.iface
    print(f"👉 Scapy Default Interface: {conf_iface}")
    return conf_iface

def run_test_scan(target_range):
    print(f"\n--- STEP 3: RUNNING TEST SCAN ON {target_range} ---")
    print("Sending 10 ARP packets... (Please wait)")
    
    try:
        # Create a simple ARP packet
        arp = scapy.ARP(pdst=target_range)
        ether = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether/arp

        # Send strictly on the default interface
        result = scapy.srp(packet, timeout=5, verbose=1)[0]
        
        print(f"\n✅ SUCCESS! Found {len(result)} devices.")
        for sent, received in result:
            print(f"   - IP: {received.psrc} | MAC: {received.hwsrc}")
            
    except Exception as e:
        print(f"\n❌ SCAN FAILED. Error: {e}")
        print("POSSIBLE FIXES:")
        print("1. Run PowerShell as ADMINISTRATOR.")
        print("2. Disable Windows Firewall temporarily.")
        print("3. Install Npcap in 'WinPcap API-compatible Mode'.")

if __name__ == "__main__":
    target = test_connectivity()
    if target:
        list_interfaces()
        run_test_scan(target)
    input("\nPress Enter to exit...")