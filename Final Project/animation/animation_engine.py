# animation/animation_engine.py

import pygame
import math

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

from animation.set_profile import get_spectrum_style


class AnimationEngine:
    def __init__(self, width=1280, height=720):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Inner Constellation")
        self.clock = pygame.time.Clock()

        # Profile / element state
        self.current_element = None          # single element fallback
        self.current_profile = None          # e.g. ["Fire", "Water", "Light"]
        self.spectrum_name = "None"          # label for UI

        # Style from set_profile
        self.style = get_spectrum_style([])  # default neutral style

        # Energy scale and temperature
        self.scale = 1.0                     # base energy size (gestures)
        self.temp_shift = 0.0                # -1.0 (cold) ~ +1.0 (warm)

        # Time and "energy" levels
        self.time = 0.0
        self.motion_level = 0.0              # 0~1, from camera motion
        self.proximity_level = 0.0           # 0~1, from APDS-9960

        # Camera motion analysis
        self.prev_gray = None
        self.downsample_size = (64, 36)

        # Orbiting orbs
        self.orbs = []  # each: [radius, angle, speed, size, color_idx]

        # Base colors per element (for single-element fallback)
        self.element_colors = {
            "Fire":   [(255, 120, 60), (255, 200, 90)],
            "Water":  [(60, 140, 255), (110, 220, 255)],
            "Wind":   [(190, 230, 255), (150, 210, 255)],
            "Earth":  [(90, 160, 100), (170, 220, 150)],
            "Light":  [(255, 255, 255), (255, 240, 210)],
            "Shadow": [(120, 70, 160), (60, 30, 100)],
        }

    # ------------------------------------------------------------------
    # Main update
    # ------------------------------------------------------------------
    def update(self, profile=None, element=None, gesture=None, proximity=None, frame=None):
        # Handle Pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

        # 1) Handle profile / element changes
        if profile is not None and profile != self.current_profile:
            self.current_profile = profile
            self.current_element = None
            self.style = get_spectrum_style(profile)
            self.spectrum_name = self.style.get("name", "Spectrum")
            self.orbs.clear()
            print(f"[Animation] Spectrum profile -> {self.spectrum_name}")

        if self.current_profile is None and element and element != self.current_element:
            self.current_element = element
            self.spectrum_name = element
            self.style = get_spectrum_style([element])  # simple fallback
            self.orbs.clear()
            print(f"[Animation] Element -> {element}")

        # 2) Gestures: up/down/left/right from APDS-9960
        if gesture:
            if gesture == "expand":
                self.scale = min(3.0, self.scale + 0.1)
            elif gesture == "shrink":
                self.scale = max(0.5, self.scale - 0.1)
            elif gesture == "cooler":
                self.temp_shift = max(-1.0, self.temp_shift - 0.05)
            elif gesture == "warmer":
                self.temp_shift = min(1.0, self.temp_shift + 0.05)

        # 3) Proximity: hand distance (0~1)
        if proximity is not None:
            # Smooth proximity for stable visuals
            self.proximity_level = 0.8 * self.proximity_level + 0.2 * proximity

        # 4) Time update
        dt_ms = self.clock.get_time()
        dt = dt_ms / 1000.0 if dt_ms > 0 else 1.0 / 60.0
        self.time += dt

        # 5) Camera motion energy (global, not body outline)
        if frame is not None and cv2 is not None and np is not None:
            self._update_motion_energy(frame)

        # 6) Breathing modulation:
        # camera motion + proximity both increase intensity
        breath_from_motion = 1.0 + 0.6 * self.motion_level
        breath_from_proximity = 1.0 + 0.8 * self.proximity_level
        breathing_wave = 1.0 + 0.18 * math.sin(self.time * 2.0 * math.pi * 0.4)

        self.scale *= 0.99
        self.scale = max(0.6, min(2.5, self.scale))

        self.render_scale = self.scale * breath_from_motion * breath_from_proximity * breathing_wave

        # Draw frame
        self._draw_frame(frame, dt)

        pygame.display.flip()
        self.clock.tick(60)

    # ------------------------------------------------------------------
    def _update_motion_energy(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_small = cv2.resize(gray, self.downsample_size)

        if self.prev_gray is None:
            self.prev_gray = gray_small
            self.motion_level = 0.0
            return

        diff = cv2.absdiff(gray_small, self.prev_gray)
        self.prev_gray = gray_small

        mean_diff = diff.mean() / 255.0
        self.motion_level = 0.85 * self.motion_level + 0.15 * min(1.0, mean_diff * 8.0)

    # ------------------------------------------------------------------
    def _draw_frame(self, frame, dt):
        # Colors from style or single element
        if self.current_profile is not None or self.current_element is not None:
            base_colors = self.style.get("base_colors", [(255, 255, 255), (200, 200, 200)])
        else:
            base_colors = [(255, 255, 255), (200, 200, 200)]

        # Background
        warm = (255, 180, 80)
        cold = (80, 150, 255)
        temp_tint = self._lerp_color(cold, warm, (self.temp_shift + 1) / 2)
        bg = self._lerp_color((0, 0, 0), temp_tint, 0.12)
        self.screen.fill(bg)

        # Camera reflection (soft)
        if frame is not None and cv2 is not None:
            self._blit_camera(frame)

        # Central aura and halo
        self._draw_aura(base_colors)

        # Orbiting element orbs
        self._update_and_draw_orbs(base_colors, dt)

        # UI label
        self._draw_label()

    # ------------------------------------------------------------------
    def _draw_aura(self, base_colors):
        aura_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        center_x = self.width // 2
        center_y = int(self.height * 0.55)

        width_factor = self.style.get("pillar_width_factor", 1.0)
        height_factor = self.style.get("pillar_height_factor", 1.0)
        halo_scale = self.style.get("halo_scale", 1.0)

        pillar_height = int(self.height * 0.6 * self.render_scale * height_factor)
        pillar_height = max(int(self.height * 0.35), min(pillar_height, int(self.height * 0.85)))

        base_width = int(140 * self.render_scale * width_factor)
        base_width = max(70, min(base_width, self.width // 2))

        base_rect = pygame.Rect(0, 0, base_width, pillar_height)
        base_rect.centerx = center_x
        base_rect.centery = center_y

        wobble = 12 * math.sin(self.time * 2.0 * math.pi * 0.3)
        base_rect.centery += int(wobble * (0.6 + 0.4 * self.proximity_level))

        num_layers = 18
        for i in range(num_layers):
            t = i / (num_layers - 1)

            if len(base_colors) == 1:
                color = base_colors[0]
            else:
                idx = int(t * (len(base_colors) - 1))
                next_idx = min(idx + 1, len(base_colors) - 1)
                local_t = (t * (len(base_colors) - 1)) - idx
                color = self._lerp_color(base_colors[idx], base_colors[next_idx], local_t)

            alpha = int(255 * (1.0 - t ** 1.4))
            # Let proximity slightly boost brightness
            alpha = int(alpha * (0.7 + 0.6 * self.proximity_level))
            alpha = max(0, min(alpha, 255))

            rgba = (color[0], color[1], color[2], alpha)

            inflate_x = int(base_width * 1.6 * t)
            inflate_y = int(pillar_height * 0.45 * t)
            layer_rect = base_rect.inflate(inflate_x, inflate_y)

            pygame.draw.ellipse(aura_surface, rgba, layer_rect)

        # Head halo
        head_y = base_rect.top + int(pillar_height * 0.18)
        halo_radius = int(base_width * 0.75 * halo_scale * (0.8 + 0.4 * self.proximity_level))
        halo_radius = max(40, halo_radius)

        halo_center = (center_x, head_y)
        for i in range(8):
            t = i / 7.0
            color = base_colors[min(len(base_colors) - 1, i % len(base_colors))]
            alpha = int(230 * (1.0 - t ** 1.8) * (0.7 + 0.5 * self.proximity_level))
            radius = int(halo_radius * (0.6 + 0.5 * t * self.render_scale))

            rgba = (color[0], color[1], color[2], max(0, min(alpha, 255)))
            pygame.draw.circle(aura_surface, rgba, halo_center, radius)

        # Core soul orb
        core_color = base_colors[len(base_colors) // 2]
        core_rgba = (core_color[0], core_color[1], core_color[2], 255)
        core_radius = int(base_width * 0.45 * (1.0 + 0.3 * self.proximity_level))
        core_radius = max(30, core_radius)
        pygame.draw.circle(aura_surface, core_rgba, halo_center, core_radius)

        self.screen.blit(aura_surface, (0, 0))

    # ------------------------------------------------------------------
    def _update_and_draw_orbs(self, base_colors, dt):
        center_x = self.width // 2
        center_y = int(self.height * 0.55)

        orb_count = self.style.get("orb_count", 24)
        r_min, r_max = self.style.get("orb_radius_range", (140, 260))
        speed_min, speed_max = self.style.get("orb_speed_range", (0.3, 0.9))
        size_min, size_max = self.style.get("orb_size_range", (4.0, 10.0))
        vertical_squash = self.style.get("orb_vertical_squash", 0.55)

        # Ensure at least orb_count orbs
        if len(self.orbs) < orb_count:
            for _ in range(orb_count - len(self.orbs)):
                radius = (r_min + (r_max - r_min) * (0.2 + 0.8 * (0.5)))
                radius = radius * (0.8 + 0.4 * self.render_scale)
                angle = math.tau * (len(self.orbs) / max(1, orb_count))
                speed = random.uniform(speed_min, speed_max)
                size = random.uniform(size_min, size_max)
                color_idx = random.randint(0, len(base_colors) - 1)
                self.orbs.append([radius, angle, speed, size, color_idx])

        # Draw orbs
        for orb in self.orbs:
            radius, angle, speed, size, color_idx = orb

            # Motion and proximity both make orbit faster
            angular_speed = speed * (1.0 + 1.2 * self.motion_level + 1.0 * self.proximity_level)
            orb[1] += angular_speed * dt

            x = center_x + math.cos(orb[1]) * radius
            y = center_y + math.sin(orb[1]) * radius * vertical_squash

            final_size = size * (0.9 + 0.7 * self.render_scale)
            final_size = max(2.0, min(final_size, 20.0))

            color = base_colors[color_idx]
            warm = (255, 180, 80)
            cold = (80, 150, 255)
            temp_tint = self._lerp_color(cold, warm, (self.temp_shift + 1) / 2)
            final_color = self._lerp_color(color, temp_tint, 0.25)

            pygame.draw.circle(self.screen, final_color, (int(x), int(y)), int(final_size))

    # ------------------------------------------------------------------
    def _blit_camera(self, frame):
        try:
            h, w = frame.shape[:2]
        except Exception:
            return

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        scale = min(self.width / w, self.height / h)
        new_size = (int(w * scale), int(h * scale))
        frame_resized = cv2.resize(frame_rgb, new_size)

        surf = pygame.surfarray.make_surface(frame_resized.swapaxes(0, 1))
        surf.set_alpha(90)
        x = (self.width - new_size[0]) // 2
        y = (self.height - new_size[1]) // 2
        self.screen.blit(surf, (x, y))

    # ------------------------------------------------------------------
    def _draw_label(self):
        font = pygame.font.SysFont("arial", 24)
        text = font.render(f"Spectrum: {self.spectrum_name}", True, (235, 235, 235))
        self.screen.blit(text, (20, 20))

        debug_font = pygame.font.SysFont("arial", 18)
        motion_text = debug_font.render(
            f"Energy(cam): {self.motion_level:.2f}", True, (220, 220, 220)
        )
        prox_text = debug_font.render(
            f"Energy(hand): {self.proximity_level:.2f}", True, (220, 220, 220)
        )
        self.screen.blit(motion_text, (20, 50))
        self.screen.blit(prox_text, (20, 70))

    # ------------------------------------------------------------------
    def _lerp_color(self, c1, c2, t):
        t = max(0.0, min(1.0, t))
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )
