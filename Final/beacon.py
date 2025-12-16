"""
beacon.py

Device: Receiving RPI

Purpose:
    - Periodically broadcast small UDP "beacon" packets.
    - The Raspberry Pi (with two ears in monitor mode) will sniff 802.11 frames
      from this Raspberry Pi Wi-Fi interface and use RSSI to estimate direction.

No monitor mode needed, just a normal Wi-Fi connection.
"""

import socket
import time
import json
import uuid

BROADCAST_PORT = 50050
BEACON_INTERVAL = 0.1  # seconds
BEACON_MAGIC = "RECEIV_BEACON_V1"


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    instance_id = str(uuid.uuid4())[:8]
    print(f"[RPI Beacon] Starting, instance id = {instance_id}")
    print(f"[RPI Beacon] Broadcasting on UDP port {BROADCAST_PORT} every {BEACON_INTERVAL}s")
    print("Press Ctrl+C to stop.")

    seq = 0
    try:
        while True:
            seq += 1
            payload = {
                "magic": BEACON_MAGIC,
                "instance": instance_id,
                "seq": seq,
                "time": time.time(),
            }
            data = json.dumps(payload).encode("utf-8")
            sock.sendto(data, ("255.255.255.255", BROADCAST_PORT))
            time.sleep(BEACON_INTERVAL)
    except KeyboardInterrupt:
        print("\n[RPI Beacon] Stopping.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
