#!/usr/bin/env python3
"""
Synchronized Display System for Multiple Raspberry Pis

This module provides a simple way to synchronize displays across multiple Pis.
One Pi broadcasts display commands, all Pis (including broadcaster) show the same thing.

Usage:
	# On the broadcaster Pi:
	from sync_display import SyncDisplay
	sync = SyncDisplay(mode='broadcast')
	sync.display_color(255, 0, 0) # All Pis show red
	sync.display_text("Hello!", color=(255, 255, 255)) # All Pis show text
	
	# On client Pis (or run both modes on broadcaster):
	from sync_display import SyncDisplay
	sync = SyncDisplay(mode='client')
	sync.start() # Will automatically display what broadcaster sends
"""

import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789
import paho.mqtt.client as mqtt
import json
import time
import uuid
import threading

# MQTT Configuration
MQTT_BROKER = 'farlab.infosci.cornell.edu'
MQTT_PORT = 1883
MQTT_TOPIC = 'IDD/syncDisplay/commands'
MQTT_USERNAME = 'idd'
MQTT_PASSWORD = 'device@theFarm'


class SyncDisplay:
	"""Synchronized display controller for multiple Pis"""
	
	def __init__(self, mode='client', display_rotation=90):
		"""
		Initialize synchronized display
		
		Args:
			mode: 'client', 'broadcast', or 'both' (client receives, broadcast sends, both does both)
			display_rotation: Display rotation (0, 90, 180, 270)
		"""
		self.mode = mode
		self.display_rotation = display_rotation
		
		# Setup display
		self.disp, self.width, self.height = self._setup_display()
		self.image = Image.new("RGB", (self.width, self.height))
		self.draw = ImageDraw.Draw(self.image)
		
		# Setup MQTT
		self.client = mqtt.Client(str(uuid.uuid1()))
		self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
		self.client.on_connect = self._on_connect
		self.client.on_message = self._on_message
		
		# Connect to MQTT
		try:
			self.client.connect(MQTT_BROKER, port=MQTT_PORT, keepalive=60)
			if self.mode in ['client', 'both']:
				self.client.loop_start()
			print(f"[OK] SyncDisplay initialized (mode={mode})")
		except Exception as e:
			print(f"[ERROR] MQTT connection failed: {e}")
	
	def _setup_display(self):
		"""Setup MiniPiTFT display"""
		# Pin configuration
		cs_pin = digitalio.DigitalInOut(board.D5)
		dc_pin = digitalio.DigitalInOut(board.D25)
		
		# Backlight
		backlight = digitalio.DigitalInOut(board.D22)
		backlight.switch_to_output()
		backlight.value = True
		
		# Create display
		spi = board.SPI()
		disp = st7789.ST7789(
			spi,
			cs=cs_pin,
			dc=dc_pin,
			rst=None,
			baudrate=64000000,
			width=135,
			height=240,
			x_offset=53,
			y_offset=40,
			rotation=self.display_rotation
		)
		
		# Get dimensions after rotation
		if self.display_rotation in [90, 270]:
			width, height = 240, 135
		else:
			width, height = 135, 240
		
		print(f"[OK] Display initialized ({width}x{height})")
		return disp, width, height
	
	def _on_connect(self, client, userdata, flags, rc):
		"""MQTT connected callback"""
		if rc == 0:
			if self.mode in ['client', 'both']:
				client.subscribe(MQTT_TOPIC)
				print(f"[OK] Subscribed to {MQTT_TOPIC}")
		else:
			print(f"[ERROR] MQTT connection failed: {rc}")
	
	def _on_message(self, client, userdata, msg):
		"""MQTT message received - execute display command"""
		try:
			cmd = json.loads(msg.payload.decode('utf-8'))
			cmd_type = cmd.get('type')
			
			if cmd_type == 'color':
				self._render_color(cmd['r'], cmd['g'], cmd['b'])
			
			elif cmd_type == 'text':
				self._render_text(
					cmd['text'],
					color=tuple(cmd.get('color', [255, 255, 255])),
					bg_color=tuple(cmd.get('bg_color', [0, 0, 0])),
					font_size=cmd.get('font_size', 20)
				)
			
			elif cmd_type == 'image':
				# For future: support image sync
				pass
			
			elif cmd_type == 'clear':
				self.clear()
			
		except Exception as e:
			print(f"[ERROR] Failed to process command: {e}")
	
	def _render_color(self, r, g, b):
		"""Render solid color on display"""
		self.draw.rectangle((0, 0, self.width, self.height), fill=(r, g, b))
		self.disp.image(self.image)
	
	def _render_text(self, text, color=(255, 255, 255), bg_color=(0, 0, 0), font_size=20):
		"""Render text on display"""
		# Clear with background color
		self.draw.rectangle((0, 0, self.width, self.height), fill=bg_color)
		
		# Load font
		try:
			font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
		except:
			font = ImageFont.load_default()
		
		# Draw text (centered)
		bbox = self.draw.textbbox((0, 0), text, font=font)
		text_width = bbox[2] - bbox[0]
		text_height = bbox[3] - bbox[1]
		x = (self.width - text_width) // 2
		y = (self.height - text_height) // 2
		
		self.draw.text((x, y), text, font=font, fill=color)
		self.disp.image(self.image)
	
	# Public API - these methods broadcast to all displays
	
	def display_color(self, r, g, b):
		"""Display solid color on all synchronized displays"""
		cmd = {
			'type': 'color',
			'r': r,
			'g': g,
			'b': b,
			'timestamp': time.time()
		}
		
		# If in both mode, render locally too
		if self.mode in ['both', 'client']:
			self._render_color(r, g, b)
		
		# If in broadcast mode, send to others
		if self.mode in ['both', 'broadcast']:
			self.client.publish(MQTT_TOPIC, json.dumps(cmd))
	
	def display_text(self, text, color=(255, 255, 255), bg_color=(0, 0, 0), font_size=20):
		"""Display text on all synchronized displays"""
		cmd = {
			'type': 'text',
			'text': text,
			'color': list(color),
			'bg_color': list(bg_color),
			'font_size': font_size,
			'timestamp': time.time()
		}
		
		# If in both mode, render locally too
		if self.mode in ['both', 'client']:
			self._render_text(text, color, bg_color, font_size)
		
		# If in broadcast mode, send to others
		if self.mode in ['both', 'broadcast']:
			self.client.publish(MQTT_TOPIC, json.dumps(cmd))
	
	def clear(self, color=(0, 0, 0)):
		"""Clear all displays"""
		self.display_color(*color)
	
	def start(self):
		"""Start client mode (blocking - keeps listening for commands)"""
		if self.mode not in ['client', 'both']:
			print("[WARNING] start() only works in client or both mode")
			return
		
		print("Listening for display commands... (Press Ctrl+C to exit)")
		try:
			while True:
				time.sleep(0.1)
		except KeyboardInterrupt:
			print("\nShutting down...")
			self.client.loop_stop()
			self.client.disconnect()
	
	def stop(self):
		"""Stop MQTT client"""
		self.client.loop_stop()
		self.client.disconnect()


# Simple test/demo
if __name__ == '__main__':
	import sys
	
	if len(sys.argv) < 2:
		print("Usage:")
		print("  python sync_display.py client    # Listen for commands")
		print("  python sync_display.py broadcast # Send test commands")
		print("  python sync_display.py both      # Do both")
		sys.exit(1)
	
	mode = sys.argv[1]
	sync = SyncDisplay(mode=mode)
	
	if mode == 'broadcast':
		print("\nSending test commands...")
		
		print("Red...")
		sync.display_color(255, 0, 0)
		time.sleep(2)
		
		print("Green...")
		sync.display_color(0, 255, 0)
		time.sleep(2)
		
		print("Blue...")
		sync.display_color(0, 0, 255)
		time.sleep(2)
		
		print("Hello World...")
		sync.display_text("Hello World!", color=(255, 255, 0), bg_color=(128, 0, 128))
		time.sleep(2)
		
		print("Done!")
		sync.stop()
	
	elif mode in ['client', 'both']:
		# If both mode, send some test commands in background
		if mode == 'both':
			def send_test_commands():
				time.sleep(3)
				colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
				for i, (r, g, b) in enumerate(colors):
					sync.display_color(r, g, b)
					time.sleep(2)
				sync.display_text("Synchronized!")
			
			threading.Thread(target=send_test_commands, daemon=True).start()
		
		sync.start()