"""
mirror.py

Device: Raspberry Pi (RECEIV)
Purpose: 
  - Listens for UDP broadcast from ROOT.
  - Displays the OPPOSITE angle (Root Angle + 180 degrees).
  - Matches the "Spin" state.
  - Uses Pygame for HDMI display.
  
Run: python3 mirror.py
"""

import socket
import json
import math
import sys
import pygame

# ---------- CONFIG ----------
PORT = 55555
WIDTH, HEIGHT = 800, 480  # Default HDMI, adjusts if fullscreen
FULLSCREEN = False

# Colors
COLOR_BG     = (0, 0, 0)
COLOR_CIRCLE = (100, 100, 100)
COLOR_TICK   = (150, 150, 150)
COLOR_TEXT   = (255, 255, 255)
COLOR_NEEDLE_NORMAL = (255, 0, 0) # Red
COLOR_NEEDLE_SPIN   = (0, 255, 0) # Green

# ---------- STATE ----------
current_angle = 0.0
is_spinning = False

# ---------- NETWORK ----------
def setup_socket():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', PORT))
    s.setblocking(False) 
    return s

# ---------- DRAWING ----------
def draw_compass(screen, font):
    screen.fill(COLOR_BG)
    cx, cy = WIDTH // 2, HEIGHT // 2
    radius = int(min(WIDTH, HEIGHT) * 0.35) 
    
    # Circle
    pygame.draw.circle(screen, COLOR_CIRCLE, (cx, cy), radius, 3)
    
    # Tick Mark
    if not is_spinning:
        pygame.draw.line(screen, COLOR_TICK, (cx, cy - radius), (cx, cy - radius + 20), 4)

    # Needle Logic (OPPOSITE)
    # If ROOT is 0 (North), Mirror is 180 (South).
    # If ROOT is 90 (Right), Mirror is 270 (-90) (Left).
    display_angle = current_angle + 180.0
    
    angle_rad = math.radians(display_angle)
    # 0 deg is UP (negative Y)
    nx = cx + radius * math.sin(angle_rad)
    ny = cy - radius * math.cos(angle_rad)
    
    color = COLOR_NEEDLE_SPIN if is_spinning else COLOR_NEEDLE_NORMAL
    width = 8 if is_spinning else 6
    
    pygame.draw.line(screen, color, (cx, cy), (nx, ny), width)
    
    # Text
    label = "MIRROR MODE"
    status_color = (100, 100, 100)
    if is_spinning:
        label = "ARRIVED!"
        status_color = (0, 255, 0)

    text_surf = font.render(label, True, status_color)
    screen.blit(text_surf, (20, 20))
    
    # Normalize for display reading (-180 to 180 range)
    read_angle = (display_angle + 180) % 360 - 180
    angle_text = font.render(f"{read_angle:.1f}", True, COLOR_TEXT)
    screen.blit(angle_text, (20, 60))

# ---------- MAIN ----------
def main():
    global current_angle, is_spinning, WIDTH, HEIGHT
    pygame.init()
    
    if FULLSCREEN:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        WIDTH, HEIGHT = screen.get_size()
    else:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        
    pygame.display.set_caption("Compass Mirror")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("dejavusans", 40)
    
    sock = setup_socket()
    print(f"[Mirror] Listening on port {PORT}...")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False

        # Network Read
        try:
            while True:
                data, addr = sock.recvfrom(1024)
                payload = json.loads(data.decode('utf-8'))
                current_angle = payload.get("angle", 0.0)
                is_spinning   = payload.get("spin", False)
        except BlockingIOError: pass
        except Exception: pass

        draw_compass(screen, font)
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
