import paho.mqtt.client as mqtt
import json
import time
import sys

try:
    import qwiic_joystick
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False
    print("qwiic_joystick not installed - hardware disabled")

class JoystickEvent:
    def __init__(self, player_number=1):
        self.player_number = player_number
        self.x = 0
        self.y = 0
        self.button = 1  # 1 = released, 0 = pressed
        self.prev_js_btn = 1
        self.mqtt_client = None
        self.js = None
        
        self.setup_mqtt()
        if HARDWARE_AVAILABLE:
            self.setup_hardware()
    
    def setup_hardware(self):
        """Initialize the Qwiic Joystick hardware"""
        try:
            self.js = qwiic_joystick.QwiicJoystick()
            if not self.js.connected:
                print(f"Qwiic Joystick not found for Player {self.player_number}", file=sys.stderr)
                self.js = None
            else:
                self.js.begin()
                print(f"Hardware joystick connected for Player {self.player_number}")
        except Exception as e:
            print(f"Hardware setup error: {e}")
            self.js = None
    
    def setup_mqtt(self):
        """Initialize MQTT connection"""
        self.mqtt_client = mqtt.Client(client_id=f"game_player{self.player_number}")
        self.mqtt_client.username_pw_set("idd", "device@theFarm")
        
        try:
            self.mqtt_client.connect("farlab.infosci.cornell.edu", 1883, 60)
            self.mqtt_client.loop_start()
            print(f"MQTT connected for Player {self.player_number}")
        except Exception as e:
            print(f"MQTT connection failed: {e}")
    
    def normalize_value(self, raw_value):
        """Convert 0-1024 range to -1 to 1"""
        return (raw_value / 512) - 1
    
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
        except Exception as e:
            print(f"Hardware read error: {e}")
            return False
    
    def check_shoot(self):
        """Check if button was pressed (transition from 1 to 0)"""
        return self.prev_js_btn == 1 and self.button == 0
    
    def send_message(self, shoot=False):
        """Send joystick state to MQTT"""
        if self.mqtt_client:
            topic = f"IDD/game/player{self.player_number}"
            payload = {
                "joy_x": self.x,
                "joy_y": self.y,
                "shoot": shoot
            }
            self.mqtt_client.publish(topic, json.dumps(payload))
            
            # Debug output
            if shoot:
                print(f"Player {self.player_number} SHOOT! at ({self.x:.2f}, {self.y:.2f})")
    
    def run(self):
        """Main hardware loop - reads joystick and publishes"""
        if self.js is None:
            print(f"No hardware available for Player {self.player_number}")
            return
        
        print(f"Joystick running for Player {self.player_number}")
        
        last_x = None
        last_y = None
        threshold = 0.05
        center_deadzone = 0.1
        
        try:
            while True:
                # Read hardware
                if self.read_hardware():
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
                        self.send_message(shoot)
                        last_x = self.x
                        last_y = self.y
                
                # 20Hz update rate
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            print(f"\n⏹ Stopping Player {self.player_number}")
            self.cleanup()
    
    # Legacy methods for manual control (web controller compatibility)
    def update_position(self, x, y):
        """Update joystick position manually and send to MQTT"""
        self.x = x
        self.y = y
        self.send_message(False)
    
    def shoot(self):
        """Trigger shoot action manually"""
        self.send_message(True)
        print(f" Player {self.player_number} SHOOT!")
    
    def cleanup(self):
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()