"""
udp_checker.py

Device: Any Raspberry Pi
Purpose: 
  - Listens for UDP broadcast from ROOT.
  - Verifies that packets are being sent and received correctly.

Run: python3 udp_checker.py --mode <send|listen>
"""

import socket
import sys
import time
import argparse

# Same port as your compass
PORT = 55555

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't actually connect, just determines route
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def run_sender():
    print(f"--- SENDER MODE (Run this on Root Pi) ---")
    print(f"My IP seems to be: {get_ip()}")
    print(f"Broadcasting to <broadcast>:{PORT}...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    count = 0
    try:
        while True:
            msg = f"Ping {count}".encode('utf-8')
            # Try generic broadcast
            sock.sendto(msg, ('<broadcast>', PORT))
            # Try explicit broadcast (often helps on Pi)
            sock.sendto(msg, ('255.255.255.255', PORT))
            
            print(f"Sent: Ping {count}")
            count += 1
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")

def run_listener():
    print(f"--- LISTENER MODE (Run this on Mirror Pi) ---")
    print(f"My IP seems to be: {get_ip()}")
    print(f"Listening on 0.0.0.0:{PORT}...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', PORT))
    sock.settimeout(5.0) # 5 second timeout
    
    try:
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                print(f"[SUCCESS] Received '{data.decode()}' from {addr}")
            except socket.timeout:
                print("[WAITING] No packets received in last 5s...")
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["send", "listen"], required=True, help="send or listen")
    args = parser.parse_args()

    if args.mode == "send":
        run_sender()
    else:
        run_listener()
