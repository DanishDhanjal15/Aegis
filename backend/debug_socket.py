import sys
# We import socket BEFORE scapy to check standard library integrity
import socket 

print(f"1. Socket Location: {getattr(socket, '__file__', 'Unknown')}")
print(f"2. Socket Type: {type(socket)}")
try:
    print(f"3. AF_INET Check: {socket.AF_INET}")
    print("✅ Standard Socket is OK.")
except AttributeError:
    print("❌ Standard Socket is BROKEN.")

# Now we import scapy to see if IT breaks socket
try:
    import scapy.all as scapy
    print("4. Scapy Imported Successfully.")
except Exception as e:
    print(f"❌ Scapy Import Failed: {e}")