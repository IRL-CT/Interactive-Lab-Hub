"""
calibrate_spin.py

Purpose:
  - Measure the RSSI (Signal Strength) at a specific "proximity radius" from the beacon.
  - Generates a configuration file 'checkpoints/spin.json'.
  
Usage:
  1. Move the Pi (Receiver) to the distance where you want the "Spinning Celebration" to start.
  2. Press [ENTER] to capture the signal strength.
  3. Move to another spot at the same distance, Press [ENTER].
  4. Type 'done' to save and exit.
"""

import os
import time
import json
import threading
import statistics
from scapy.all import sniff, Dot11, RadioTap

# ---------- CONFIG ----------

RECEIV_MAC  = "2c:cf:67:73:fe:2c"  # Beacon MAC
LEFT_IFACE  = "wlan1"
RIGHT_IFACE = "wlan2"
CHECKPOINT_DIR = "checkpoints"

# ---------- STATE ----------

lock = threading.Lock()
# We use a tiny buffer just to get a stable reading for "this moment"
rssi_recent = [] 

captured_thresholds = []

# ---------- UTILS ----------

def ensure_root():
    if os.geteuid() != 0:
        raise SystemExit("!! MUST RUN AS ROOT (sudo) !!")

def normalize_mac(mac):
    return (mac or "").lower()

TARGET_MAC = normalize_mac(RECEIV_MAC)

def sniff_thread(iface, side):
    def packet_handler(pkt):
        global rssi_recent
        if not pkt.haslayer(Dot11): return
        if normalize_mac(pkt.addr2) == TARGET_MAC:
            try:
                val = int(pkt[RadioTap].dBm_AntSignal)
                with lock:
                    rssi_recent.append(val)
                    if len(rssi_recent) > 20: # Keep only last 20 packets
                        rssi_recent.pop(0)
            except: pass
    
    print(f"[Sniffer] Listening on {iface}...")
    sniff(iface=iface, prn=packet_handler, store=False)

def get_strongest_signal():
    """Returns the max RSSI seen recently (max is better than avg for proximity)."""
    with lock:
        if not rssi_recent: return None
        return max(rssi_recent)

# ---------- MAIN ----------

def main():
    ensure_root()
    if not os.path.exists(CHECKPOINT_DIR): os.makedirs(CHECKPOINT_DIR)

    # Start Sniffers
    t1 = threading.Thread(target=sniff_thread, args=(LEFT_IFACE, "left"), daemon=True)
    t2 = threading.Thread(target=sniff_thread, args=(RIGHT_IFACE, "right"), daemon=True)
    t1.start(); t2.start()

    print("\n" + "="*50)
    print("  PROXIMITY (SPIN) CALIBRATION")
    print("="*50)
    print("Waiting for signal...")

    while True:
        if get_strongest_signal() is not None: break
        time.sleep(0.5)

    print("\nSignal found!")
    print("INSTRUCTIONS:")
    print("1. Stand at the EDGE of the circle where you want the 'Spin Mode' to trigger.")
    print("2. Press [ENTER] to record the signal strength there.")
    print("3. Type 'done' to save.")

    while True:
        user_input = input("\n[Press ENTER to Record / Type 'done' to Save] > ").strip().lower()
        
        if user_input == 'done':
            if not captured_thresholds:
                print("No points recorded. Exiting without save.")
                break
            
            # Calculate Threshold
            # We use the AVERAGE of the recorded points.
            # If the signal is STRONGER (greater) than this, we spin.
            avg_thresh = statistics.mean(captured_thresholds)
            
            # Add a tiny safety margin (-2dB) so it triggers slightly inside the radius
            final_thresh = avg_thresh
            
            data = {"spin_threshold_dbm": final_thresh}
            path = os.path.join(CHECKPOINT_DIR, "spin.json")
            
            with open(path, "w") as f:
                json.dump(data, f)
            
            print(f"\n[SAVED] Spin Threshold: {final_thresh:.1f} dBm")
            print(f"Saved to: {path}")
            break
        else:
            # Capture
            strength = get_strongest_signal()
            if strength is None:
                print("!! Signal lost temporarily. Wait a second...")
                continue
            
            print(f"   Recorded signal strength: {strength} dBm")
            captured_thresholds.append(strength)

if __name__ == "__main__":
    main()
