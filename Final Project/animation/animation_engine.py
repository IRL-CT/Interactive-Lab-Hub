# animation/animation_engine.py

import pygame
import math
import random

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
        self.spectrum_name = "None"          # style name label

        # Style from set_profile
        self.style = get_spectrum_style([])  # default neutral style

        # Energy scale and temperature
        self.scale = 1.0                     # base energy size (gestures)
        self.temp_shift = 0.0                # -1.0 (cold) ~ +1.0 (warm)

        # Time and energy levels
        self.time = 0.0
        self.motion_level = 0.0              # 0~1, from camera motion
        self.proximity_level = 0.0           # 0~1, from APDS-9960

        # Camera motion analysis
        self.prev_gray = None
        self.downsample_size = (64, 36)

        # Shared state for patterns that need persistent particles
        self.orbs = []

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

        if self.current_profile is None and element is not None and element != self.current_element:
            self.current_element = element
            self.spectrum_name = element
            self.style = get_spectrum_style([element])
            self.orbs.clear()
            print(f"[Animation] Element -> {element}")

        # 2) Gestures from APDS-9960
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
            self.proximity_level = 0.8 * self.proximity_level + 0.2 * proximity

        # 4) Time update
        dt_ms = self.clock.get_time()
        dt = dt_ms / 1000.0 if dt_ms > 0 else 1.0 / 60.0
        self.time += dt

        # 5) Camera motion energy (global)
        if frame is not None and cv2 is not None and np is not None:
            self._update_motion_energy(frame)

        # 6) Breathing modulation
        breath_from_motion = 1.0 + 0.7 * self.motion_level
        breath_from_proximity = 1.0 + 0.9 * self.proximity_level
        breathing_wave = 1.0 + 0.22 * math.sin(self.time * 2.0 * math.pi * 0.4)

        self.scale *= 0.99
        self.scale = max(0.7, min(2.7, self.scale))

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
        # Colors from style or fallback
        if self.current_profile is not None or self.current_element is not None:
            base_colors = self.style.get("base_colors", [(255, 255, 255), (200, 200, 200)])
        else:
            base_colors = [(255, 255, 255), (200, 200, 200)]

        # Background tint
        warm = (255, 190, 90)
        cold = (70, 150, 255)
        temp_tint = self._lerp_color(cold, warm, (self.temp_shift + 1) / 2)
        bg = self._lerp_color((0, 0, 0), temp_tint, 0.18)
        self.screen.fill(bg)

        # Camera reflection (subtle)
        if frame is not None and cv2 is not None:
            self._blit_camera(frame)

        # Pattern routing
        pattern_type = self.style.get("pattern_type", "pillar_orbs")

        if pattern_type == "pillar_orbs":
            self._pattern_pillar_orbs(base_colors, dt)
        elif pattern_type == "ring_waves":
            self._pattern_ring_waves(base_colors)
        elif pattern_type == "radial_rays":
            self._pattern_radial_rays(base_colors)
        elif pattern_type == "galaxy":
            self._pattern_galaxy(base_colors)
        elif pattern_type == "double_pillar":
            self._pattern_double_pillar(base_colors)
        elif pattern_type == "vertical_ribbons":
            self._pattern_vertical_ribbons(base_colors)
        elif pattern_type == "grid_pulse":
            self._pattern_grid_pulse(base_colors)
        elif pattern_type == "starfield":
            self._pattern_starfield(base_colors)
        elif pattern_type == "vortex":
            self._pattern_vortex(base_colors)
        elif pattern_type == "cross_waves":
            self._pattern_cross_waves(base_colors)
        else:
            # fallback
            self._pattern_pillar_orbs(base_colors, dt)

        # UI label
        self._draw_label()

    # ------------------------------------------------------------------
    # PATTERN 1: central pillar + orbiting orbs
    # ------------------------------------------------------------------
    def _pattern_pillar_orbs(self, base_colors, dt):
        self._draw_aura_center(base_colors)
        self._pattern_orbiting_orbs(base_colors, dt)

    def _draw_aura_center(self, base_colors):
        aura_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        center_x = self.width // 2
        center_y = int(self.height * 0.55)

        width_factor = self.style.get("pillar_width_factor", 1.0)
        height_factor = self.style.get("pillar_height_factor", 1.0)
        halo_scale = self.style.get("halo_scale", 1.0)

        pillar_height = int(self.height * 0.7 * self.render_scale * height_factor)
        pillar_height = max(int(self.height * 0.4), min(pillar_height, int(self.height * 0.9)))

        base_width = int(200 * self.render_scale * width_factor)
        base_width = max(90, min(base_width, int(self.width * 0.75)))

        base_rect = pygame.Rect(0, 0, base_width, pillar_height)
        base_rect.centerx = center_x
        base_rect.centery = center_y

        wobble = 18 * math.sin(self.time * 2.0 * math.pi * 0.3)
        base_rect.centery += int(wobble * (0.6 + 0.4 * self.proximity_level))

        num_layers = 22
        for i in range(num_layers):
            t = i / (num_layers - 1)

            if len(base_colors) == 1:
                color = base_colors[0]
            else:
                idx = int(t * (len(base_colors) - 1))
                next_idx = min(idx + 1, len(base_colors) - 1)
                local_t = (t * (len(base_colors) - 1)) - idx
                color = self._lerp_color(base_colors[idx], base_colors[next_idx], local_t)

            alpha = int(255 * (1.0 - t ** 1.3))
            alpha = int(alpha * (0.9 + 0.8 * self.proximity_level))
            alpha = max(0, min(alpha, 255))

            rgba = (color[0], color[1], color[2], alpha)

            inflate_x = int(base_width * 1.8 * t)
            inflate_y = int(pillar_height * 0.5 * t)
            layer_rect = base_rect.inflate(inflate_x, inflate_y)

            pygame.draw.ellipse(aura_surface, rgba, layer_rect)

        # Head halo
        head_y = base_rect.top + int(pillar_height * 0.2)
        halo_radius = int(base_width * 0.9 * halo_scale * (0.8 + 0.5 * self.proximity_level))
        halo_radius = max(55, halo_radius)

        halo_center = (center_x, head_y)
        for i in range(10):
            t = i / 9.0
            color = base_colors[min(len(base_colors) - 1, i % len(base_colors))]
            alpha = int(245 * (1.0 - t ** 1.8) * (0.8 + 0.5 * self.proximity_level))
            radius = int(halo_radius * (0.6 + 0.5 * t * self.render_scale))

            rgba = (color[0], color[1], color[2], max(0, min(alpha, 255)))
            pygame.draw.circle(aura_surface, rgba, halo_center, radius)

        # Core orb
        core_color = base_colors[len(base_colors) // 2]
        core_rgba = (core_color[0], core_color[1], core_color[2], 255)
        core_radius = int(base_width * 0.55 * (1.0 + 0.3 * self.proximity_level))
        core_radius = max(40, core_radius)
        pygame.draw.circle(aura_surface, core_rgba, halo_center, core_radius)

        self.screen.blit(aura_surface, (0, 0))

    def _pattern_orbiting_orbs(self, base_colors, dt):
        center_x = self.width // 2
        center_y = int(self.height * 0.55)

        orb_count = self.style.get("orb_count", 32)
        r_min, r_max = self.style.get("orb_radius_range", (160, 320))
        speed_min, speed_max = self.style.get("orb_speed_range", (0.4, 1.0))
        size_min, size_max = self.style.get("orb_size_range", (5.0, 12.0))
        vertical_squash = self.style.get("orb_vertical_squash", 0.55)

        if len(self.orbs) < orb_count:
            for _ in range(orb_count - len(self.orbs)):
                radius = random.uniform(r_min, r_max) * (0.7 + 0.4 * self.render_scale)
                angle = random.uniform(0, math.tau)
                speed = random.uniform(speed_min, speed_max)
                size = random.uniform(size_min, size_max)
                color_idx = random.randint(0, len(base_colors) - 1)
                self.orbs.append([radius, angle, speed, size, color_idx])

        for orb in self.orbs:
            radius, angle, speed, size, color_idx = orb

            angular_speed = speed * (1.0 + 1.3 * self.motion_level + 1.1 * self.proximity_level)
            orb[1] += angular_speed * dt

            x = center_x + math.cos(orb[1]) * radius
            y = center_y + math.sin(orb[1]) * radius * vertical_squash

            final_size = size * (1.1 + 0.8 * self.render_scale)
            final_size = max(3.0, min(final_size, 26.0))

            color = base_colors[color_idx]
            warm = (255, 190, 90)
            cold = (70, 150, 255)
            temp_tint = self._lerp_color(cold, warm, (self.temp_shift + 1) / 2)
            final_color = self._lerp_color(color, temp_tint, 0.25)

            pygame.draw.circle(self.screen, final_color, (int(x), int(y)), int(final_size))

    # ------------------------------------------------------------------
    # PATTERN 2: ring waves
    # ------------------------------------------------------------------
    def _pattern_ring_waves(self, base_colors):
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        center_x = self.width // 2
        center_y = int(self.height * 0.55)

        num_rings = 18
        base_radius_y = 60 * self.render_scale
        gap = 26 * self.render_scale

        amp = 36 * (0.3 + 0.7 * (self.motion_level + self.proximity_level) / 2.0)
        time_factor = self.time * 1.4

        for i in range(num_rings):
            t = i / (num_rings - 1)
            radius_y = base_radius_y + i * gap
            radius_x = radius_y * 2.0

            y_offset = math.sin(time_factor + i * 0.35) * amp

            if len(base_colors) == 1:
                color = base_colors[0]
            else:
                idx = int(t * (len(base_colors) - 1))
                next_idx = min(idx + 1, len(base_colors) - 1)
                local_t = (t * (len(base_colors) - 1)) - idx
                color = self._lerp_color(base_colors[idx], base_colors[next_idx], local_t)

            alpha = int(230 * (1.0 - t ** 1.5))
            alpha = int(alpha * (0.7 + 0.8 * self.proximity_level))
            alpha = max(0, min(alpha, 255))

            rect = pygame.Rect(0, 0, int(radius_x * 2), int(radius_y * 2))
            rect.centerx = center_x
            rect.centery = center_y + int(y_offset)

            rgba = (color[0], color[1], color[2], alpha)
            pygame.draw.ellipse(surface, rgba, rect, width=4)

        self.screen.blit(surface, (0, 0))

    # ------------------------------------------------------------------
    # PATTERN 3: radial rays
    # ------------------------------------------------------------------
    def _pattern_radial_rays(self, base_colors):
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        center_x = self.width // 2
        center_y = int(self.height * 0.55)

        num_rays = 24
        inner_radius = 60 * (0.9 + 0.4 * self.render_scale)
        outer_base = min(self.width, self.height) * 0.8 * (0.6 + 0.6 * self.render_scale)

        energy = (self.motion_level + self.proximity_level) / 2.0
        time_factor = self.time * (1.0 + 1.4 * energy)

        for i in range(num_rays):
            t = i / num_rays
            angle = t * math.tau + time_factor

            if len(base_colors) == 1:
                color = base_colors[0]
            else:
                idx = int(t * (len(base_colors) - 1))
                next_idx = min(idx + 1, len(base_colors) - 1)
                local_t = (t * (len(base_colors) - 1)) - idx
                color = self._lerp_color(base_colors[idx], base_colors[next_idx], local_t)

            length = outer_base * (0.7 + 0.7 * energy + 0.25 * math.sin(self.time * 2.3 + i * 0.5))

            x1 = center_x + math.cos(angle) * inner_radius
            y1 = center_y + math.sin(angle) * inner_radius
            x2 = center_x + math.cos(angle) * length
            y2 = center_y + math.sin(angle) * length

            alpha = int(255 * (0.5 + 0.6 * energy))
            rgba = (color[0], color[1], color[2], max(0, min(alpha, 255)))

            width = int(4 + 5 * self.render_scale)
            for offset in range(-width // 2, width // 2 + 1):
                dx = -math.sin(angle) * offset * 0.7
                dy = math.cos(angle) * offset * 0.7
                start_pos = (int(x1 + dx), int(y1 + dy))
                end_pos = (int(x2 + dx), int(y2 + dy))
                pygame.draw.line(surface, rgba, start_pos, end_pos, 1)

        self.screen.blit(surface, (0, 0))

    # ------------------------------------------------------------------
    # PATTERN 4: galaxy
    # ------------------------------------------------------------------
    def _pattern_galaxy(self, base_colors):
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        center_x = self.width // 2
        center_y = int(self.height * 0.55)

        num_arms = 5
        points_per_arm = 80
        base_radius = 60 * self.render_scale
        max_radius = min(self.width, self.height) * 0.6 * (0.7 + 0.6 * self.render_scale)

        energy = (self.motion_level + self.proximity_level) / 2.0
        spin_speed = 0.5 + 1.0 * energy

        for arm in range(num_arms):
            arm_angle = arm * (math.tau / num_arms)
            for i in range(points_per_arm):
                t = i / (points_per_arm - 1)
                radius = base_radius + t * max_radius

                angle = arm_angle + t * 2.3 + self.time * spin_speed

                jitter = (0.5 - random.random()) * 18.0
                x = center_x + math.cos(angle) * radius + jitter
                y = center_y + math.sin(angle) * radius * 0.75 + jitter

                if len(base_colors) == 1:
                    color = base_colors[0]
                else:
                    idx = int(t * (len(base_colors) - 1))
                    next_idx = min(idx + 1, len(base_colors) - 1)
                    local_t = (t * (len(base_colors) - 1)) - idx
                    color = self._lerp_color(base_colors[idx], base_colors[next_idx], local_t)

                alpha = int(255 * (0.15 + 0.85 * (1.0 - t)))
                alpha = int(alpha * (0.4 + 0.9 * energy))
                alpha = max(0, min(alpha, 255))

                size = 2 + int(4 * (1.0 - t) * (0.8 + 0.7 * self.render_scale))

                rgba = (color[0], color[1], color[2], alpha)
                pygame.draw.circle(surface, rgba, (int(x), int(y)), size)

        self.screen.blit(surface, (0, 0))

    # ------------------------------------------------------------------
    # PATTERN 5: double pillar (left & right)
    # ------------------------------------------------------------------
    def _pattern_double_pillar(self, base_colors):
        aura_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        center_y = int(self.height * 0.55)
        spacing = int(self.width * 0.22)

        centers = [
            (self.width // 2 - spacing, center_y),
            (self.width // 2 + spacing, center_y),
        ]

        pillar_height = int(self.height * 0.6 * self.render_scale)
        pillar_height = max(int(self.height * 0.4), min(pillar_height, int(self.height * 0.9)))

        base_width = int(140 * self.render_scale)
        base_width = max(70, min(base_width, int(self.width * 0.4)))

        wobble_amp = 12 * (1.0 + 0.5 * self.proximity_level)

        for cx, cy in centers:
            base_rect = pygame.Rect(0, 0, base_width, pillar_height)
            base_rect.centerx = cx
            base_rect.centery = cy + int(wobble_amp * math.sin(self.time * 2.0 + cx * 0.002))

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

                alpha = int(240 * (1.0 - t ** 1.4) * (0.7 + 0.7 * self.proximity_level))
                alpha = max(0, min(alpha, 255))
                rgba = (color[0], color[1], color[2], alpha)

                inflate_x = int(base_width * 1.4 * t)
                inflate_y = int(pillar_height * 0.5 * t)
                layer_rect = base_rect.inflate(inflate_x, inflate_y)

                pygame.draw.ellipse(aura_surface, rgba, layer_rect)

        # Soft bridge between two pillars
        mid_rect = pygame.Rect(0, 0, spacing * 2, int(pillar_height * 0.35))
        mid_rect.center = (self.width // 2, center_y)
        bridge_color = base_colors[len(base_colors) // 2]
        bridge_rgba = (bridge_color[0], bridge_color[1], bridge_color[2], 120 + int(80 * self.proximity_level))
        pygame.draw.ellipse(aura_surface, bridge_rgba, mid_rect)

        self.screen.blit(aura_surface, (0, 0))

    # ------------------------------------------------------------------
    # PATTERN 6: vertical ribbons
    # ------------------------------------------------------------------
    def _pattern_vertical_ribbons(self, base_colors):
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        num_ribbons = 10
        ribbon_width = self.width / num_ribbons

        energy = (self.motion_level + self.proximity_level) / 2.0

        for i in range(num_ribbons):
            t = i / max(1, num_ribbons - 1)

            if len(base_colors) == 1:
                color = base_colors[0]
            else:
                idx = int(t * (len(base_colors) - 1))
                next_idx = min(idx + 1, len(base_colors) - 1)
                local_t = (t * (len(base_colors) - 1)) - idx
                color = self._lerp_color(base_colors[idx], base_colors[next_idx], local_t)

            alpha = int(200 * (0.7 + 0.6 * energy))
            rgba = (color[0], color[1], color[2], max(0, min(alpha, 255)))

            x_center = (i + 0.5) * ribbon_width
            # horizontal wobble
            wobble = math.sin(self.time * 1.5 + i * 0.7) * ribbon_width * 0.25 * (0.4 + 0.6 * energy)
            rect = pygame.Rect(0, 0, int(ribbon_width * 0.9), int(self.height * (0.7 + 0.4 * self.render_scale)))
            rect.centerx = int(x_center + wobble)
            rect.centery = int(self.height * 0.55)

            pygame.draw.rect(surface, rgba, rect, border_radius=40)

        self.screen.blit(surface, (0, 0))

    # ------------------------------------------------------------------
    # PATTERN 7: grid pulse
    # ------------------------------------------------------------------
    def _pattern_grid_pulse(self, base_colors):
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        rows = 10
        cols = 16
        cell_w = self.width / cols
        cell_h = self.height / rows

        energy = (self.motion_level + self.proximity_level) / 2.0

        for r in range(rows):
            for c in range(cols):
                t_x = c / max(1, cols - 1)
                t_y = r / max(1, rows - 1)
                t = (t_x + t_y) / 2.0

                if len(base_colors) == 1:
                    color = base_colors[0]
                else:
                    idx = int(t * (len(base_colors) - 1))
                    next_idx = min(idx + 1, len(base_colors) - 1)
                    local_t = (t * (len(base_colors) - 1)) - idx
                    color = self._lerp_color(base_colors[idx], base_colors[next_idx], local_t)

                phase = self.time * 2.0 + c * 0.5 + r * 0.4
                pulse = (math.sin(phase) + 1.0) / 2.0  # 0~1

                alpha = int(255 * pulse * (0.4 + 0.8 * energy))
                if alpha < 25:
                    continue

                size = int(min(cell_w, cell_h) * (0.25 + 0.5 * pulse) * (0.8 + 0.6 * self.render_scale))
                x = int((c + 0.5) * cell_w)
                y = int((r + 0.5) * cell_h)

                rgba = (color[0], color[1], color[2], max(0, min(alpha, 255)))
                pygame.draw.circle(surface, rgba, (x, y), size)

        self.screen.blit(surface, (0, 0))

    # ------------------------------------------------------------------
    # PATTERN 8: starfield
    # ------------------------------------------------------------------
    def _pattern_starfield(self, base_colors):
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        energy = (self.motion_level + self.proximity_level) / 2.0
        num_stars = int(260 * (0.8 + 0.7 * self.render_scale))

        random.seed(42)  # stable pattern per frame for softness

        for i in range(num_stars):
            t = random.random()

            if len(base_colors) == 1:
                color = base_colors[0]
            else:
                idx = int(t * (len(base_colors) - 1))
                next_idx = min(idx + 1, len(base_colors) - 1)
                local_t = (t * (len(base_colors) - 1)) - idx
                color = self._lerp_color(base_colors[idx], base_colors[next_idx], local_t)

            x = random.randint(0, self.width)
            y = random.randint(0, self.height)

            flicker = (math.sin(self.time * 3.0 + i * 0.21) + 1.0) / 2.0
            alpha = int(255 * (0.2 + 0.8 * flicker) * (0.4 + 0.8 * energy))
            alpha = max(0, min(alpha, 255))

            size = 1 + int(3 * (0.3 + 0.7 * flicker) * (0.7 + 0.7 * self.render_scale))

            rgba = (color[0], color[1], color[2], alpha)
            pygame.draw.circle(surface, rgba, (x, y), size)

        self.screen.blit(surface, (0, 0))

    # ------------------------------------------------------------------
    # PATTERN 9: vortex
    # ------------------------------------------------------------------
    def _pattern_vortex(self, base_colors):
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        center_x = self.width // 2
        center_y = int(self.height * 0.55)

        num_rings = 16
        max_radius = min(self.width, self.height) * 0.55 * (0.8 + 0.6 * self.render_scale)

        energy = (self.motion_level + self.proximity_level) / 2.0
        spin = self.time * (1.2 + 1.0 * energy)

        for i in range(num_rings):
            t = i / (num_rings - 1)
            radius = (t ** 1.1) * max_radius

            if len(base_colors) == 1:
                color = base_colors[0]
            else:
                idx = int(t * (len(base_colors) - 1))
                next_idx = min(idx + 1, len(base_colors) - 1)
                local_t = (t * (len(base_colors) - 1)) - idx
                color = self._lerp_color(base_colors[idx], base_colors[next_idx], local_t)

            alpha = int(220 * (1.0 - t ** 1.4) * (0.6 + 0.8 * energy))
            alpha = max(0, min(alpha, 255))

            angle_offset = spin + t * 3.0

            num_segments = 64
            points = []
            for j in range(num_segments):
                a = j / (num_segments - 1) * math.tau + angle_offset
                x = center_x + math.cos(a) * radius
                y = center_y + math.sin(a) * radius * 0.65
                points.append((int(x), int(y)))

            rgba = (color[0], color[1], color[2], alpha)
            if len(points) > 1:
                pygame.draw.lines(surface, rgba, True, points, width=3)

        self.screen.blit(surface, (0, 0))

    # ------------------------------------------------------------------
    # PATTERN 10: cross waves (horizontal + vertical)
    # ------------------------------------------------------------------
    def _pattern_cross_waves(self, base_colors):
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        energy = (self.motion_level + self.proximity_level) / 2.0

        # Horizontal bands
        num_h = 8
        for i in range(num_h):
            t = i / max(1, num_h - 1)

            if len(base_colors) == 1:
                color = base_colors[0]
            else:
                idx = int(t * (len(base_colors) - 1))
                next_idx = min(idx + 1, len(base_colors) - 1)
                local_t = (t * (len(base_colors) - 1)) - idx
                color = self._lerp_color(base_colors[idx], base_colors[next_idx], local_t)

            y = int((i + 0.5) * self.height / num_h + math.sin(self.time * 1.5 + i) * 25 * (0.4 + 0.6 * energy))
            alpha = int(190 * (0.6 + 0.7 * energy))
            rgba = (color[0], color[1], color[2], max(0, min(alpha, 255)))

            rect = pygame.Rect(0, y - 18, self.width, 36)
            pygame.draw.rect(surface, rgba, rect)

        # Vertical bands
        num_v = 8
        for j in range(num_v):
            t = j / max(1, num_v - 1)

            if len(base_colors) == 1:
                color = base_colors[0]
            else:
                idx = int(t * (len(base_colors) - 1))
                next_idx = min(idx + 1, len(base_colors) - 1)
                local_t = (t * (len(base_colors) - 1)) - idx
                color = self._lerp_color(base_colors[idx], base_colors[next_idx], local_t)

            x = int((j + 0.5) * self.width / num_v + math.cos(self.time * 1.3 + j) * 25 * (0.4 + 0.6 * energy))
            alpha = int(160 * (0.6 + 0.7 * energy))
            rgba = (color[0], color[1], color[2], max(0, min(alpha, 255)))

            rect = pygame.Rect(x - 18, 0, 36, self.height)
            pygame.draw.rect(surface, rgba, rect)

        self.screen.blit(surface, (0, 0))

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
        surf.set_alpha(70)
        x = (self.width - new_size[0]) // 2
        y = (self.height - new_size[1]) // 2
        self.screen.blit(surf, (x, y))

    # ------------------------------------------------------------------
    def _draw_label(self):
        font = pygame.font.SysFont("arial", 26)
        title = f"Energy Field: {self.spectrum_name}"
        text = font.render(title, True, (245, 245, 245))
        self.screen.blit(text, (20, 18))

        # Show selected elements (profile) or current element
        if self.current_profile:
            elements_str = " · ".join(self.current_profile)
        elif self.current_element:
            elements_str = self.current_element
        else:
            elements_str = "None"

        sub_font = pygame.font.SysFont("arial", 22)
        profile_text = sub_font.render(f"Elements: {elements_str}", True, (230, 230, 230))
        self.screen.blit(profile_text, (20, 50))

        debug_font = pygame.font.SysFont("arial", 16)
        motion_text = debug_font.render(
            f"Energy(cam): {self.motion_level:.2f}", True, (220, 220, 220)
        )
        prox_text = debug_font.render(
            f"Energy(hand): {self.proximity_level:.2f}", True, (220, 220, 220)
        )
        self.screen.blit(motion_text, (20, 80))
        self.screen.blit(prox_text, (20, 100))

    # ------------------------------------------------------------------
    def _lerp_color(self, c1, c2, t):
        t = max(0.0, min(1.0, t))
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )

    # ------------------------------------------------------------------
    # Public: reset current profile / element from outside
    # ------------------------------------------------------------------
    def reset_profile(self):
        """Clear current energy field so a new profile can be selected."""
        self.current_profile = None
        self.current_element = None
        self.spectrum_name = "None"
        self.style = get_spectrum_style([])  # back to neutral style
        self.orbs.clear()
        print("[Animation] Profile cleared. Waiting for new selection.")


