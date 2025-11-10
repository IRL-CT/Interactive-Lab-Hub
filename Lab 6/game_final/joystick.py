import paho.mqtt.client as mqtt
import json
import time
import sys

try:
    import qwiic_joystick
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False
    print("WARNING: qwiic_joystick not installed - hardware disabled")

class JoystickEvent:
    def __init__(self, player_number=1):
        self.player_number = player_number
        self.x = 0
        self.y = 0
        self.button = 1  # 1 = released, 0 = pressed
        self.prev_js_btn = 1
        self.mqtt_client = None
        self.js = None
        self.mqtt_connected = False
        
        self.setup_mqtt()
        if HARDWARE_AVAILABLE:
            self.setup_hardware()
    
    def setup_hardware(self):
        """Initialize the Qwiic Joystick hardware"""
        try:
            self.js = qwiic_joystick.QwiicJoystick()
            if not self.js.connected:
                print(f"[WARN] Qwiic Joystick not found for Player {self.player_number}", file=sys.stderr)
                self.js = None
            else:
                self.js.begin()
                print(f"[OK] Hardware joystick connected for Player {self.player_number}")
        except Exception as e:
            print(f"[FAIL] Hardware setup error Player {self.player_number}: {e}")
            self.js = None
    
    def on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.mqtt_connected = True
            print(f"[OK] MQTT connected for Player {self.player_number}")
        else:
            self.mqtt_connected = False
            print(f"[FAIL] MQTT connection failed for Player {self.player_number}: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.mqtt_connected = False
        print(f"[FAIL] MQTT disconnected for Player {self.player_number}: {rc}")
    
    def setup_mqtt(self):
        """Initialize MQTT connection with reconnection support"""
        client_id = f"game_player{self.player_number}_{int(time.time())}"
        self.mqtt_client = mqtt.Client(client_id=client_id)
        self.mqtt_client.username_pw_set("idd", "device@theFarm")
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_disconnect = self.on_disconnect
        
        # Enable automatic reconnection
        self.mqtt_client.reconnect_delay_set(min_delay=1, max_delay=120)
        
        try:
            self.mqtt_client.connect("farlab.infosci.cornell.edu", 1883, 60)
            self.mqtt_client.loop_start()
            print(f"[OK] MQTT setup initiated for Player {self.player_number}")
        except Exception as e:
            print(f"[FAIL] MQTT connection failed for Player {self.player_number}: {e}")
    
    def normalize_value(self, raw_value):
        """Convert 0-1024 range to -1 to 1"""
        normalized = (raw_value / 512.0) - 1.0
        # Clamp to -1 to 1 range
        return max(-1.0, min(1.0, normalized))
    
    def read_hardware(self):
        """Read from physical joystick"""
        if self.js is None:
            return False
        
        try:
            # Read raw values
            raw_x = self.js.horizontal
            raw_y = self.js.vertical
            
            # Normalize to -1 to 1
            self.x = self.normalize_value(raw_x)
            self.y = self.normalize_value(raw_y)
            
            # Update button state
            self.prev_js_btn = self.button
            self.button = self.js.button  # 0 = pressed, 1 = released
            
            return True
        except OSError as e:
            print(f"[FAIL] I2C read error for Player {self.player_number}: {e}")
            return False
        except Exception as e:
            print(f"[FAIL] Hardware read error for Player {self.player_number}: {e}")
            return False
    
    def check_shoot(self):
        """Check if button was pressed (transition from 1 to 0)"""
        return self.prev_js_btn == 1 and self.button == 0
    
    def send_message(self, shoot=False):
        """Send joystick state to MQTT"""
        if self.mqtt_client and self.mqtt_connected:
            topic = f"IDD/game/player{self.player_number}"
            payload = {
                "joy_x": round(self.x, 3),
                "joy_y": round(self.y, 3),
                "shoot": shoot,
                "timestamp": time.time()
            }
            
            try:
                result = self.mqtt_client.publish(topic, json.dumps(payload))
                
                # Debug output for shoots
                if shoot:
                    print(f"[SHOOT] Player {self.player_number} SHOOT! at ({self.x:.2f}, {self.y:.2f})")
                
                return result.rc == mqtt.MQTT_ERR_SUCCESS
            except Exception as e:
                print(f"[FAIL] MQTT publish error for Player {self.player_number}: {e}")
                return False
        else:
            if not self.mqtt_connected:
                print(f"[WARN] MQTT not connected for Player {self.player_number}")
            return False
    
    def run(self):
        """Main hardware loop - reads joystick and publishes"""
        if not HARDWARE_AVAILABLE:
            print(f"[WARN] Hardware not available for Player {self.player_number} - exiting")
            return
        
        if self.js is None:
            print(f"[WARN] No hardware joystick for Player {self.player_number} - exiting")
            return
        
        print(f"[JOY] Joystick running for Player {self.player_number}")
        
        last_x = None
        last_y = None
        threshold = 0.05
        center_deadzone = 0.1
        
        consecutive_errors = 0
        max_errors = 10
        
        try:
            while True:
                # Read hardware
                if self.read_hardware():
                    consecutive_errors = 0  # Reset error counter on success
                    
                    # Check for shoot
                    shoot = self.check_shoot()
                    
                    # Check if joystick is moved away from center
                    is_moved = abs(self.x) > center_deadzone or abs(self.y) > center_deadzone
               
                    position_changed = (
                        last_x is None or 
                        last_y is None or
                        abs(self.x - last_x) > threshold or 
                        abs(self.y - last_y) > threshold
                    )
                    
                    # Only send if shooting OR (moved AND position changed)
                    if shoot or (is_moved and position_changed):
                        if self.send_message(shoot):
                            last_x = self.x
                            last_y = self.y
                else:
                    consecutive_errors += 1
                    if consecutive_errors >= max_errors:
                        print(f"[FAIL] Too many consecutive errors for Player {self.player_number}, stopping")
                        break
                
                # 20Hz update rate
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            print(f"\n[STOP] Stopping Player {self.player_number}")
        except Exception as e:
            print(f"[FAIL] Fatal error in joystick loop for Player {self.player_number}: {e}")
        finally:
            self.cleanup()
    
    # Legacy methods for manual control (web controller compatibility)
    def update_position(self, x, y):
        """Update joystick position manually and send to MQTT"""
        self.x = max(-1.0, min(1.0, x))
        self.y = max(-1.0, min(1.0, y))
        self.send_message(False)
    
    def shoot(self):
        """Trigger shoot action manually"""
        self.send_message(True)
        print(f"[SHOOT] Player {self.player_number} SHOOT!")
    
    def cleanup(self):
        """Clean up resources"""
        print(f"[CLEAN] Cleaning up Player {self.player_number}")
        if self.mqtt_client:
            try:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
            except:
                pass


# Test mode - run standalone
if __name__ == "__main__":
    import sys
    
    player = 1
    if len(sys.argv) > 1:
        try:
            player = int(sys.argv[1])
        except:
            player = 1
    
    print(f"Starting joystick test for Player {player}")
    print("Press Ctrl+C to stop")
    
    joystick = JoystickEvent(player_number=player)
    joystick.run()