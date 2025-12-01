# animation/animation_engine.py
"""
Inner Constellation - Animation Engine
Author: Joy

Usage:
    from animation.animation_engine import AnimationEngine

    engine = AnimationEngine(width=1280, height=720)
    while True:
        state = {...}  # from SensorManager
        engine.update(state)
"""

import math
import random
from typing import Dict, Optional

import numpy as np
import pygame


# ---------- Helper functions ----------

def lerp_color(c1, c2, t: float):
    """Linear interpolation between two RGB colors."""
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


# ---------- Particle classes ----------

class Particle:
    """
    Simple particle used for all elements.
    Behavior (speed, drift, alpha) is tuned by element config.
    """

    def __init__(self, x, y, vx, vy, radius, color, life, drift=0.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.base_color = color
        self.life = life
        self.age = 0.0
        self.drift = drift  # used e.g. for Wind / Shadow

    def update(self, dt, width, height):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        # simple wrap-around
        if self.x < -50:
            self.x = width + 50
        elif self.x > width + 50:
            self.x = -50
        if self.y < -50:
            self.y = height + 50
        elif self.y > height + 50:
            self.y = -50

        # optional drift
        self.vx += self.drift * dt * (random.random() - 0.5)
        self.vy += self.drift * dt * (random.random() - 0.5)

    def is_dead(self):
        return self.age >= self.life

    def get_alpha(self):
        # fade in & out
        t = self.age / self.life
        if t < 0.2:
            return t / 0.2
        elif t > 0.8:
            return (1.0 - t) / 0.2
        else:
            return 1.0


# ---------- Main Animation Engine ----------

class AnimationEngine:
    """
    Core drawing engine.
    Input: state dict from SensorManager, e.g.
        {
            "element": "Fire",
            "scale": 1.2,
            "color_temperature": 0.1,
            "camera_frame": <numpy array (H,W,3) BGR or None>
        }
    """

    def __init__(self, width=1280, height=720, use_camera_blend=True):
        pygame.init()
        pygame.display.set_caption("Inner Constellation")
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()

        # semi-transparent layer for trail / glow
        self.trail_surface = pygame.Surface((width, height), pygame.SRCALPHA)

        self.use_camera_blend = use_camera_blend

        # element configuration
        self.element_configs = {
            "Fire": {
                "base_colors": [(255, 120, 40), (255, 200, 80)],
                "bg_color": (10, 2, 0),
                "speed": 120,
                "radius": (4, 10),
                "life": (2.0, 4.0),
                "drift": 5.0,
            },
            "Water": {
                "base_colors": [(60, 120, 255), (120, 220, 255)],
                "bg_color": (0, 5, 15),
                "speed": 60,
                "radius": (5, 12),
                "life": (3.0, 6.0),
                "drift": 10.0,
            },
            "Wind": {
                "base_colors": [(180, 220, 255), (220, 255, 255)],
                "bg_color": (5, 8, 18),
                "speed": 180,
                "radius": (2, 6),
                "life": (1.5, 3.0),
                "drift": 25.0,
            },
            "Earth": {
                "base_colors": [(80, 150, 90), (160, 210, 140)],
                "bg_color": (5, 12, 8),
                "speed": 40,
                "radius": (6, 14),
                "life": (4.0, 7.0),
                "drift": 3.0,
            },
            "Light": {
                "base_colors": [(255, 255, 255), (255, 240, 200)],
                "bg_color": (10, 10, 20),
                "speed": 80,
                "radius": (6, 12),
                "life": (2.5, 4.5),
                "drift": 15.0,
            },
            "Shadow": {
                "base_colors": [(120, 60, 160), (40, 10, 80)],
                "bg_color": (3, 0, 8),
                "speed": 50,
                "radius": (5, 12),
                "life": (3.0, 6.0),
                "drift": 18.0,
            },
        }

        self.current_element: Optional[str] = None
        self.particles = []
        self.time_accum = 0.0

    # --------- Particle management ----------

    def _spawn_particles(self, element_cfg, count: int, scale: float):
        for _ in range(count):
            x = random.uniform(0, self.width)
            y = random.uniform(0, self.height)
            angle = random.uniform(0, math.tau)
            speed = element_cfg["speed"] * (0.5 + random.random()) * scale
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            r_min, r_max = element_cfg["radius"]
            radius = random.uniform(r_min, r_max) * scale

            life_min, life_max = element_cfg["life"]
            life = random.uniform(life_min, life_max)

            color = random.choice(element_cfg["base_colors"])

            p = Particle(
                x=x,
                y=y,
                vx=vx,
                vy=vy,
                radius=radius,
                color=color,
                life=life,
                drift=element_cfg["drift"],
            )
            self.particles.append(p)

    def _ensure_particles(self, element_cfg, scale: float):
        target_count = int(180 * scale)
        if len(self.particles) < target_count:
            self._spawn_particles(element_cfg, target_count - len(self.particles), scale)

    # --------- Camera blending ----------

    def _blend_camera_frame(self, frame: np.ndarray):
        """
        Blend camera frame softly into background.
        frame is expected in BGR (OpenCV style).
        """
        if frame is None:
            return

        # Resize to screen
        fh, fw = frame.shape[:2]
        scale = min(self.width / fw, self.height / fh)
        new_size = (int(fw * scale), int(fh * scale))
        frame_resized = cv2.resize(frame, new_size)

        # Convert BGR -> RGB
        frame_rgb = frame_resized[:, :, ::1][:, :, ::-1]

        surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
        surface.set_alpha(70)  # transparency
        x = (self.width - new_size[0]) // 2
        y = (self.height - new_size[1]) // 2
        self.screen.blit(surface, (x, y))

    # --------- Main update/draw ----------

    def update(self, state: Dict):
        """
        Called once per frame by main loop.
        """
        # Handle pygame events so window doesn't freeze
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

        dt = self.clock.tick(60) / 1000.0  # seconds, capped at 60 FPS

        element = state.get("element") or self.current_element or "Fire"
        scale = float(state.get("scale", 1.0))
        color_temp = float(state.get("color_temperature", 0.0))
        camera_frame = state.get("camera_frame", None)

        # Change element: reset particles
        if element != self.current_element:
            self.current_element = element
            self.particles.clear()

        cfg = self.element_configs.get(self.current_element, self.element_configs["Fire"])

        # Background: slightly translucent fill to create trail
        bg = cfg["bg_color"]
        self.screen.fill(bg)

        # Optional: blend camera reflection
        if self.use_camera_blend and camera_frame is not None:
            try:
                import cv2  # only import if needed
                self._blend_camera_frame(camera_frame)
            except ImportError:
                # no cv2 installed, silently skip
                pass

        # fade previous particles (trail surface)
        self.trail_surface.fill((0, 0, 0, 35))  # alpha-only fade
        self._ensure_particles(cfg, scale)

        # Update + draw particles
        for p in list(self.particles):
            p.update(dt, self.width, self.height)
            if p.is_dead():
                self.particles.remove(p)
                continue

            alpha = p.get_alpha()

            # Apply color temperature shift: negative = cooler, positive = warmer
            warm_color = (255, 180, 100)
            cool_color = (100, 160, 255)
            t = (color_temp + 1.0) / 2.0  # map [-1,1] -> [0,1]
            tint = lerp_color(cool_color, warm_color, t)
            final_color = lerp_color(p.base_color, tint, 0.35)

            radius = max(1, int(p.radius))
            s = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
            pygame.draw.circle(
                s,
                final_color + (int(180 * alpha),),
                (radius * 2, radius * 2),
                radius,
            )
            self.trail_surface.blit(s, (p.x - radius * 2, p.y - radius * 2))

        # composite trail onto screen
        self.screen.blit(self.trail_surface, (0, 0))

        # Optional: simple element label in corner
        self._draw_label(self.current_element)

        pygame.display.flip()

    def _draw_label(self, element_name: str):
        font = pygame.font.SysFont("arial", 20)
        text = font.render(f"Element: {element_name}", True, (230, 230, 230))
        self.screen.blit(text, (20, 20))
