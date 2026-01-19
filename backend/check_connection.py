import scapy.all as scapy
import socket
import sys

# Force UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')

def check_network():
    print("--- DIAGNOSTIC START ---")
    
    # --- FIX IS HERE: Use socket.AF_INET, not socket.socket.AF_INET ---
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        my_ip = s.getsockname()[0]
        s.close()
        print(f"MY IP ADDRESS: {my_ip}")
        
        # Calculate subnet
        ip_parts = my_ip.split('.')
        target_range = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
        print(f"SCAN TARGET:   {target_range}")
        
    except Exception as e:
        print(f"ERROR detecting IP: {e}")
        return

    print(f"SCAPY INTERFACE: {scapy.conf.iface}")
    
    print("\n[Sending 10 Probe Packets...]")
    try:
        arp = scapy.ARP(pdst=target_range)
        ether = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether/arp

        result = scapy.srp(packet, timeout=4, verbose=1)[0]
        
        print(f"\nRESULT: Found {len(result)} devices.")
        for sent, received in result:
            print(f" - IP: {received.psrc}  (MAC: {received.hwsrc})")

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        print("Note: Run as ADMINISTRATOR.")

if __name__ == "__main__":
    check_network()
    input("\nPress Enter to close...")