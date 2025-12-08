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
        self.current_element = None          
        self.current_profile = None          
        self.spectrum_name = "None"          

        # Style dictionary from set_profile
        self.style = get_spectrum_style([])  # neutral default style

        # Energy scale and temperature
        self.scale = 1.0                     # base energy size
        self.temp_shift = 0.0               # -1.0 (cold) ~ +1.0 (warm)

        # Time and camera-derived energy levels
        self.time = 0.0
        self.motion_level = 0.0             

        # Camera motion analysis
        self.prev_gray = None
        self.downsample_size = (64, 36)

        self.body_x = 0.5   # 0 = left, 1 = right
        self.body_y = 0.5   # 0 = top, 1 = bottom

        self.size_level = 0.0               # larger = closer

        self.orbs = []
        self.comets = []
        self.bloom_orbs = []

        self.stroke_boost = 2  

        # Fallback 单元素颜色
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
        """
        Main update entry point.

        Args:
            profile: list of 3 elements (or None)
            element: single element name (fallback before profile is selected)
            gesture: ignored (gesture sensor disabled; camera-only control)
            proximity: ignored
            frame: OpenCV camera frame (BGR) or None
        """
        # Handle window close
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

        # 1) Profile / element 
        if profile is not None and profile != self.current_profile:
            self.current_profile = profile
            self.current_element = None
            self.style = get_spectrum_style(profile)
            self.spectrum_name = self.style.get("name", "Spectrum")
            self._clear_dynamic_buffers()
            print(f"[Animation] Spectrum profile -> {self.spectrum_name}")

        if self.current_profile is None and element is not None and element != self.current_element:
            self.current_element = element
            self.spectrum_name = element
            self.style = get_spectrum_style([element])
            self._clear_dynamic_buffers()
            print(f"[Animation] Element -> {element}")

        # 2) 
        dt_ms = self.clock.get_time()
        dt = dt_ms / 1000.0 if dt_ms > 0 else 1.0 / 60.0
        self.time += dt

        # 3) motion + position + size
        if frame is not None and cv2 is not None and np is not None:
            self._update_motion_features(frame)

        # 4) body_x → temp_shift (-1 ~ +1)
        target_temp = (self.body_x - 0.5) * 2.0
        target_temp = max(-1.0, min(1.0, target_temp))
        self.temp_shift = 0.9 * self.temp_shift + 0.1 * target_temp

        # 5) size_level to scale
        base_scale = 1.5
        target_scale = base_scale + (0.9 - 1.6 * self.size_level)
        self.scale = 0.9 * self.scale + 0.1 * target_scale
        self.scale = max(0.6, min(3.0, self.scale))

        # 6) 
        breath_from_motion = 1.0 + 0.9 * self.motion_level
        breathing_wave = 1.0 + 0.28 * math.sin(self.time * 2.0 * math.pi * 0.4)
        self.render_scale = self.scale * breath_from_motion * breathing_wave

        # 7) frame
        self._draw_frame(frame, dt)

        pygame.display.flip()
        self.clock.tick(60)

    # ------------------------------------------------------------------
    def _clear_dynamic_buffers(self):
        self.orbs.clear()
        self.comets.clear()
        self.bloom_orbs.clear()

    # ------------------------------------------------------------------
    def _update_motion_features(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_small = cv2.resize(gray, self.downsample_size)

        if self.prev_gray is None:
            self.prev_gray = gray_small
            self.motion_level = 0.0
            self.size_level = 0.0
            return

        diff = cv2.absdiff(gray_small, self.prev_gray)
        self.prev_gray = gray_small

        mean_diff = diff.mean() / 255.0
        self.motion_level = 0.85 * self.motion_level + 0.15 * min(1.0, mean_diff * 8.0)

        diff_norm = diff.astype("float32") / 255.0
        mask = diff_norm > 0.18
        active_ratio = mask.mean()
        size_raw = min(1.0, active_ratio * 18.0)
        self.size_level = 0.9 * self.size_level + 0.1 * size_raw

        total = diff.sum()
        if total > 1:
            h, w = diff.shape
            ys, xs = np.indices((h, w))
            cx = (diff * xs).sum() / total
            cy = (diff * ys).sum() / total

            norm_x = float(cx) / max(1.0, w - 1)
            norm_y = float(cy) / max(1.0, h - 1)

            self.body_x = 0.85 * self.body_x + 0.15 * norm_x
            self.body_y = 0.85 * self.body_y + 0.15 * norm_y

    # ------------------------------------------------------------------
    def _get_body_center(self):
        x = int(self.width * (0.15 + 0.7 * self.body_x))   # 15%~85% width
        y = int(self.height * (0.25 + 0.5 * self.body_y))  # 25%~75% height
        return x, y

    # ------------------------------------------------------------------
    def _draw_frame(self, frame, dt):
        # 1) 
        if self.current_profile is not None or self.current_element is not None:
            base_colors = self.style.get(
                "base_colors", [(255, 255, 255), (200, 200, 200)]
            )
        else:
            base_colors = [(255, 255, 255), (200, 200, 200)]

        # 2) night-sky
        bg_color = self.style.get("background_color", (5, 7, 18))
        self.screen.fill(bg_color)

        # 3) 
        temp_t = (self.temp_shift + 1) / 2.0
        temp_t = max(0.0, min(1.0, temp_t))

        cold_core = (80, 150, 255)
        warm_core = (255, 190, 110)
        tint_target = self._lerp_color(cold_core, warm_core, temp_t)

        tinted_colors = []
        for c in base_colors:
            tinted = self._lerp_color(c, tint_target, 0.65)
            boosted = self._boost_color(tinted, factor=1.5)
            tinted_colors.append(boosted)

        # 4) 
        if frame is not None and cv2 is not None:
            self._blit_camera(frame)

        # 5) Pattern 
        pattern_type = self.style.get("pattern_type", "pillar_orbs")

        if pattern_type == "pillar_orbs":
            self._pattern_pillar_orbs(tinted_colors, dt)
        elif pattern_type == "ring_waves":
            self._pattern_ring_waves(tinted_colors)
        elif pattern_type == "radial_rays":
            self._pattern_radial_rays(tinted_colors)
        elif pattern_type == "galaxy":
            self._pattern_galaxy(tinted_colors)
        elif pattern_type == "double_pillar":
            self._pattern_double_pillar(tinted_colors)
        elif pattern_type == "vertical_ribbons":
            self._pattern_vertical_ribbons(tinted_colors)
        elif pattern_type == "grid_pulse":
            self._pattern_grid_pulse(tinted_colors)
        elif pattern_type == "starfield":
            self._pattern_starfield(tinted_colors)
        elif pattern_type == "vortex":
            self._pattern_vortex(tinted_colors)
        elif pattern_type == "cross_waves":
            self._pattern_cross_waves(tinted_colors)
        elif pattern_type == "aurora":
            self._pattern_aurora(tinted_colors)
        elif pattern_type == "blooming_orbs":
            self._pattern_blooming_orbs(tinted_colors, dt)
        elif pattern_type == "comet_trails":
            self._pattern_comet_trails(tinted_colors, dt)
        elif pattern_type == "spiral_rings":
            self._pattern_spiral_rings(tinted_colors)
        else:
            self._pattern_pillar_orbs(tinted_colors, dt)

        # 6) 
        self._draw_label()

    # ------------------------------------------------------------------
    # PATTERN 1: central pillar + orbiting orbs
    # ------------------------------------------------------------------
    def _pattern_pillar_orbs(self, base_colors, dt):
        self._draw_aura_center(base_colors)
        self._pattern_orbiting_orbs(base_colors, dt)

    def _draw_aura_center(self, base_colors):
        aura_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        center_x, center_y = self._get_body_center()

        width_factor = self.style.get("pillar_width_factor", 1.0)
        height_factor = self.style.get("pillar_height_factor", 1.0)
        halo_scale = self.style.get("halo_scale", 1.0)

        pillar_height = int(self.height * 0.7 * self.render_scale * height_factor)
        pillar_height = max(int(self.height * 0.4), min(pillar_height, int(self.height * 0.9)))

        base_width = int(220 * self.render_scale * width_factor)
        base_width = max(110, min(base_width, int(self.width * 0.8)))

        base_rect = pygame.Rect(0, 0, base_width, pillar_height)
        base_rect.centerx = center_x
        base_rect.centery = center_y

        wobble = 22 * math.sin(self.time * 2.0 * math.pi * 0.35)
        base_rect.centery += int(wobble * (0.7 + 0.5 * self.motion_level))

        num_layers = 24
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
            alpha = int(alpha * (0.9 + 0.9 * self.motion_level))
            alpha = max(0, min(alpha, 255))

            rgba = (color[0], color[1], color[2], alpha)

            inflate_x = int(base_width * 2.0 * t)
            inflate_y = int(pillar_height * 0.5 * t)
            layer_rect = base_rect.inflate(inflate_x, inflate_y)

            pygame.draw.ellipse(aura_surface, rgba, layer_rect)

        # 
        head_y = base_rect.top + int(pillar_height * 0.2)
        halo_radius = int(base_width * 1.0 * halo_scale * (0.9 + 0.7 * self.motion_level))
        halo_radius = max(65, halo_radius)

        halo_center = (center_x, head_y)
        for i in range(10):
            t = i / 9.0
            color = base_colors[min(len(base_colors) - 1, i % len(base_colors))]
            alpha = int(250 * (1.0 - t ** 1.8) * (0.8 + 0.6 * self.motion_level))
            radius = int(halo_radius * (0.6 + 0.5 * t * self.render_scale))

            rgba = (color[0], color[1], color[2], max(0, min(alpha, 255)))
            pygame.draw.circle(aura_surface, rgba, halo_center, radius)

        core_color = base_colors[len(base_colors) // 2]
        core_rgba = (core_color[0], core_color[1], core_color[2], 255)
        core_radius = int(base_width * 0.6 * (1.0 + 0.4 * self.motion_level))
        core_radius = max(45, core_radius)
        pygame.draw.circle(aura_surface, core_rgba, halo_center, core_radius)

        self.screen.blit(aura_surface, (0, 0))

    def _pattern_orbiting_orbs(self, base_colors, dt):
        center_x, center_y = self._get_body_center()

        orb_count = self.style.get("orb_count", 36)
        r_min, r_max = self.style.get("orb_radius_range", (180, 360))
        speed_min, speed_max = self.style.get("orb_speed_range", (0.6, 1.3))
        size_min, size_max = self.style.get("orb_size_range", (6.0, 14.0))
        vertical_squash = self.style.get("orb_vertical_squash", 0.55)

        if len(self.orbs) < orb_count:
            for _ in range(orb_count - len(self.orbs)):
                radius = random.uniform(r_min, r_max) * (0.7 + 0.5 * self.render_scale)
                angle = random.uniform(0, math.tau)
                speed = random.uniform(speed_min, speed_max)
                size = random.uniform(size_min, size_max)
                color_idx = random.randint(0, len(base_colors) - 1)
                self.orbs.append([radius, angle, speed, size, color_idx])

        for orb in self.orbs:
            radius, angle, speed, size, color_idx = orb

            angular_speed = speed * (1.0 + 1.4 * self.motion_level)
            orb[1] += angular_speed * dt

            x = center_x + math.cos(orb[1]) * radius
            y = center_y + math.sin(orb[1]) * radius * vertical_squash

            final_size = size * (1.1 + 1.0 * self.render_scale)
            final_size = max(4.0, min(final_size, 30.0))

            color = base_colors[color_idx]
            pygame.draw.circle(self.screen, color, (int(x), int(y)), int(final_size))

    # ------------------------------------------------------------------
    # PATTERN 2: ring waves
    # ------------------------------------------------------------------
    def _pattern_ring_waves(self, base_colors):
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        center_x, center_y = self._get_body_center()

        num_rings = 18
        base_radius_y = 70 * self.render_scale
        gap = 30 * self.render_scale

        amp = 40 * (0.3 + 0.7 * self.motion_level)
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

            alpha = int(240 * (1.0 - t ** 1.5))
            alpha = int(alpha * (0.7 + 0.9 * self.motion_level))
            alpha = max(0, min(alpha, 255))

            rect = pygame.Rect(0, 0, int(radius_x * 2), int(radius_y * 2))
            rect.centerx = center_x
            rect.centery = center_y + int(y_offset)

            rgba = (color[0], color[1], color[2], alpha)
            ring_width = int(5 * self.stroke_boost)
            pygame.draw.ellipse(surface, rgba, rect, width=ring_width)

        self.screen.blit(surface, (0, 0))

    # ------------------------------------------------------------------
    # PATTERN 3: radial rays
    # ------------------------------------------------------------------
    def _pattern_radial_rays(self, base_colors):
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        center_x, center_y = self._get_body_center()

        num_rays = 24
        inner_radius = 70 * (0.9 + 0.4 * self.render_scale)
        outer_base = min(self.width, self.height) * 0.85 * (0.6 + 0.6 * self.render_scale)

        energy = self.motion_level
        time_factor = self.time * (1.0 + 1.6 * energy)

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

            length = outer_base * (
                0.7
                + 0.9 * energy
                + 0.3 * math.sin(self.time * 2.6 + i * 0.5)
            )

            x1 = center_x + math.cos(angle) * inner_radius
            y1 = center_y + math.sin(angle) * inner_radius
            x2 = center_x + math.cos(angle) * length
            y2 = center_y + math.sin(angle) * length

            alpha = int(255 * (0.55 + 0.7 * energy))
            rgba = (color[0], color[1], color[2], max(0, min(alpha, 255)))

            width = int((5 + 6 * self.render_scale) * self.stroke_boost)
            for offset in range(-width // 2, width // 2 + 1):
                dx = -math.sin(angle) * offset * 0.8
                dy = math.cos(angle) * offset * 0.8
                start_pos = (int(x1 + dx), int(y1 + dy))
                end_pos = (int(x2 + dx), int(y2 + dy))
                pygame.draw.line(surface, rgba, start_pos, end_pos, 1)

        self.screen.blit(surface, (0, 0))

    # ------------------------------------------------------------------
    # PATTERN 4: galaxy
    # ------------------------------------------------------------------
    def _pattern_galaxy(self, base_colors):
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        center_x, center_y = self._get_body_center()

        num_arms = 5
        points_per_arm = 80
        base_radius = 70 * self.render_scale
        max_radius = min(self.width, self.height) * 0.65 * (0.7 + 0.6 * self.render_scale)

        energy = self.motion_level
        spin_speed = 0.6 + 1.2 * energy

        for arm in range(num_arms):
            arm_angle = arm * (math.tau / num_arms)
            for i in range(points_per_arm):
                t = i / (points_per_arm - 1)
                radius = base_radius + t * max_radius

                angle = arm_angle + t * 2.5 + self.time * spin_speed

                jitter = (0.5 - random.random()) * 20.0
                x = center_x + math.cos(angle) * radius + jitter
                y = center_y + math.sin(angle) * radius * 0.75 + jitter

                if len(base_colors) == 1:
                    color = base_colors[0]
                else:
                    idx = int(t * (len(base_colors) - 1))
                    next_idx = min(idx + 1, len(base_colors) - 1)
                    local_t = (t * (len(base_colors) - 1)) - idx
                    color = self._lerp_color(base_colors[idx], base_colors[next_idx], local_t)

                alpha = int(255 * (0.15 + 0.9 * (1.0 - t)))
                alpha = int(alpha * (0.4 + 1.0 * energy))
                alpha = max(0, min(alpha, 255))

                size = 2 + int(4 * (1.0 - t) * (0.8 + 0.9 * self.render_scale))

                rgba = (color[0], color[1], color[2], alpha)
                pygame.draw.circle(surface, rgba, (int(x), int(y)), size)

        self.screen.blit(surface, (0, 0))

    # ------------------------------------------------------------------
    # PATTERN 5: double pillar
    # ------------------------------------------------------------------
    def _pattern_double_pillar(self, base_colors):
        aura_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        base_cx, cy = self._get_body_center()
        spacing = int(self.width * 0.18)

        centers = [
            (base_cx - spacing, cy),
            (base_cx + spacing, cy),
        ]

        pillar_height = int(self.height * 0.6 * self.render_scale)
        pillar_height = max(int(self.height * 0.4), min(pillar_height, int(self.height * 0.9)))

        base_width = int(150 * self.render_scale)
        base_width = max(80, min(base_width, int(self.width * 0.45)))

        wobble_amp = 15 * (1.0 + 0.6 * self.motion_level)

        for idx_c, (cx, cy) in enumerate(centers):
            base_rect = pygame.Rect(0, 0, base_width, pillar_height)
            base_rect.centerx = cx
            base_rect.centery = cy + int(wobble_amp * math.sin(self.time * 2.0 + idx_c * 0.7))

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

                alpha = int(240 * (1.0 - t ** 1.4) * (0.7 + 0.9 * self.motion_level))
                alpha = max(0, min(alpha, 255))
                rgba = (color[0], color[1], color[2], alpha)

                inflate_x = int(base_width * 1.5 * t)
                inflate_y = int(pillar_height * 0.5 * t)
                layer_rect = base_rect.inflate(inflate_x, inflate_y)

                pygame.draw.ellipse(aura_surface, rgba, layer_rect)

        mid_rect = pygame.Rect(0, 0, spacing * 2, int(pillar_height * 0.35))
        mid_rect.center = (base_cx, cy)
        bridge_color = base_colors[len(base_colors) // 2]
        bridge_rgba = (
            bridge_color[0],
            bridge_color[1],
            bridge_color[2],
            130 + int(90 * self.motion_level),
        )
        pygame.draw.ellipse(aura_surface, bridge_rgba, mid_rect)

        self.screen.blit(aura_surface, (0, 0))

    # ------------------------------------------------------------------
    # PATTERN 6: vertical ribbons
    # ------------------------------------------------------------------
    def _pattern_vertical_ribbons(self, base_colors):
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        num_ribbons = 10
        ribbon_width = self.width / num_ribbons
        energy = self.motion_level

        for i in range(num_ribbons):
            t = i / max(1, num_ribbons - 1)

            if len(base_colors) == 1:
                color = base_colors[0]
            else:
                idx = int(t * (len(base_colors) - 1))
                next_idx = min(idx + 1, len(base_colors) - 1)
                local_t = (t * (len(base_colors) - 1)) - idx
                color = self._lerp_color(base_colors[idx], base_colors[next_idx], local_t)

            alpha = int(210 * (0.7 + 0.7 * energy))
            rgba = (color[0], color[1], color[2], max(0, min(alpha, 255)))

            x_center = (i + 0.5) * ribbon_width
            wobble = math.sin(self.time * 1.5 + i * 0.7) * ribbon_width * 0.25 * (
                0.4 + 0.6 * energy
            )
            rect = pygame.Rect(
                0, 0,
                int(ribbon_width * 0.9),
                int(self.height * (0.7 + 0.5 * self.render_scale))
            )
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

        energy = self.motion_level

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

                alpha = int(255 * pulse * (0.4 + 0.9 * energy))
                if alpha < 25:
                    continue

                size = int(
                    min(cell_w, cell_h)
                    * (0.26 + 0.55 * pulse)
                    * (0.8 + 0.8 * self.render_scale)
                )
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

        energy = self.motion_level
        num_stars = int(260 * (0.9 + 0.9 * self.render_scale))

        random.seed(42)  

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
            alpha = int(
                255
                * (0.22 + 0.88 * flicker)
                * (0.4 + 1.0 * energy)
            )
            alpha = max(0, min(alpha, 255))

            size = 1 + int(
                3 * (0.35 + 0.65 * flicker) * (0.8 + 0.8 * self.render_scale)
            )

            rgba = (color[0], color[1], color[2], alpha)
            pygame.draw.circle(surface, rgba, (x, y), size)

        self.screen.blit(surface, (0, 0))

    # ------------------------------------------------------------------
    # PATTERN 9: vortex
    # ------------------------------------------------------------------
    def _pattern_vortex(self, base_colors):
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        center_x, center_y = self._get_body_center()

        num_rings = 16
        max_radius = min(self.width, self.height) * 0.6 * (0.8 + 0.7 * self.render_scale)

        energy = self.motion_level
        spin = self.time * (1.4 + 1.2 * energy)

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

            alpha = int(
                230
                * (1.0 - t ** 1.4)
                * (0.6 + 0.9 * energy)
            )
            alpha = max(0, min(alpha, 255))

            angle_offset = spin + t * 3.0

            num_segments = 64
            points = []
            for j in range(num_segments):
                a = j / (num_segments - 1) * math.tau + angle_offset
                x = center_x + math.cos(a) * radius
                y = center_y + math.sin(a) * radius * 0.7
                points.append((int(x), int(y)))

            rgba = (color[0], color[1], color[2], alpha)
            if len(points) > 1:
                line_width = int(4 * self.stroke_boost)
                pygame.draw.lines(surface, rgba, True, points, width=line_width)

        self.screen.blit(surface, (0, 0))

    # ------------------------------------------------------------------
    # PATTERN 10: cross waves
    # ------------------------------------------------------------------
    def _pattern_cross_waves(self, base_colors):
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        energy = self.motion_level

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

            y = int(
                (i + 0.5) * self.height / num_h
                + math.sin(self.time * 1.5 + i) * 30 * (0.4 + 0.6 * energy)
            )
            alpha = int(200 * (0.6 + 0.8 * energy))
            rgba = (color[0], color[1], color[2], max(0, min(alpha, 255)))

            half_h = int(20 * self.stroke_boost)
            rect = pygame.Rect(0, y - half_h, self.width, half_h * 2)
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

            x = int(
                (j + 0.5) * self.width / num_v
                + math.cos(self.time * 1.3 + j) * 30 * (0.4 + 0.6 * energy)
            )
            alpha = int(170 * (0.6 + 0.8 * energy))
            rgba = (color[0], color[1], color[2], max(0, min(alpha, 255)))

            half_w = int(20 * self.stroke_boost)
            rect = pygame.Rect(x - half_w, 0, half_w * 2, self.height)
            pygame.draw.rect(surface, rgba, rect)

        self.screen.blit(surface, (0, 0))

    # ------------------------------------------------------------------
    # PATTERN 11: aurora
    # ------------------------------------------------------------------
    def _pattern_aurora(self, base_colors):
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        energy = self.motion_level

        bands = 4
        band_height = int(self.height * 0.28)

        for i in range(bands):
            t = i / max(1, bands - 1)

            if len(base_colors) == 1:
                color = base_colors[0]
            else:
                idx = int(t * (len(base_colors) - 1))
                next_idx = min(idx + 1, len(base_colors) - 1)
                local_t = (t * (len(base_colors) - 1)) - idx
                color = self._lerp_color(base_colors[idx], base_colors[next_idx], local_t)

            alpha = int(210 * (0.5 + 0.6 * energy))
            rgba = (color[0], color[1], color[2], max(0, min(alpha, 255)))

            for x in range(0, self.width, 8):
                phase = (x / self.width) * math.tau + self.time * 0.9 + i * 0.7
                y = int(
                    band_height * 0.2
                    + (band_height * 0.4 + i * 30) * (0.4 + 0.6 * energy)
                    + math.sin(phase) * 35 * (0.4 + 0.8 * energy)
                )
                rect = pygame.Rect(x, y, 12, band_height)
                pygame.draw.rect(surface, rgba, rect)

        self.screen.blit(surface, (0, 0))

    # ------------------------------------------------------------------
    # PATTERN 12: blooming orbs
    # ------------------------------------------------------------------
    def _pattern_blooming_orbs(self, base_colors, dt):
        center_x, center_y = self._get_body_center()
        energy = self.motion_level

        # Spawn new orbs
        target_count = int(50 * (0.5 + self.render_scale * 0.6))
        while len(self.bloom_orbs) < target_count:
            angle = random.uniform(0, math.tau)
            dist = random.uniform(30, min(self.width, self.height) * 0.4)
            spawn_x = center_x + math.cos(angle) * dist
            spawn_y = center_y + math.sin(angle) * dist * 0.8

            max_radius = random.uniform(15, 45) * (0.7 + 0.7 * self.render_scale)
            life = random.uniform(1.0, 3.0)
            color_idx = random.randint(0, len(base_colors) - 1)

            self.bloom_orbs.append([spawn_x, spawn_y, 0.0, max_radius, life, color_idx])

        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        new_list = []

        for x, y, age, max_r, life, color_idx in self.bloom_orbs:
            age += dt
            if age > life:
                continue

            t = age / life
            radius = max_r * t
            fade = (1.0 - t) ** 1.8

            color = base_colors[color_idx]
            alpha = int(255 * fade * (0.6 + 0.9 * energy))
            alpha = max(0, min(alpha, 255))

            rgba = (color[0], color[1], color[2], alpha)
            pygame.draw.circle(surface, rgba, (int(x), int(y)), int(radius))

            new_list.append([x, y, age, max_r, life, color_idx])

        self.bloom_orbs = new_list
        self.screen.blit(surface, (0, 0))

    # ------------------------------------------------------------------
    # PATTERN 13: comet trails
    # ------------------------------------------------------------------
    def _pattern_comet_trails(self, base_colors, dt):
        center_x, center_y = self._get_body_center()
        energy = self.motion_level

        target_count = 25
        while len(self.comets) < target_count:
            radius = random.uniform(120, min(self.width, self.height) * 0.5)
            angle = random.uniform(0, math.tau)
            speed = random.uniform(0.4, 1.2)
            tail = random.randint(10, 25)
            color_idx = random.randint(0, len(base_colors) - 1)
            self.comets.append([radius, angle, speed, tail, color_idx])

        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        new_list = []

        for radius, angle, speed, tail, color_idx in self.comets:
            angular_speed = speed * (1.0 + 1.3 * energy)
            angle += angular_speed * dt

            color = base_colors[color_idx]
            for i in range(tail):
                t = i / max(1, tail - 1)
                a = angle - t * 0.5
                r = radius * (0.7 + 0.3 * t)

                x = center_x + math.cos(a) * r
                y = center_y + math.sin(a) * r * 0.8

                alpha = int(255 * (1.0 - t) * (0.4 + 0.9 * energy))
                alpha = max(0, min(alpha, 255))
                size = int(8 * (1.0 - t) * (0.6 + 0.8 * self.render_scale))

                rgba = (color[0], color[1], color[2], alpha)
                pygame.draw.circle(surface, rgba, (int(x), int(y)), max(1, size))

            new_list.append([radius, angle, speed, tail, color_idx])

        self.comets = new_list
        self.screen.blit(surface, (0, 0))

    # ------------------------------------------------------------------
    # PATTERN 14: spiral rings
    # ------------------------------------------------------------------
    def _pattern_spiral_rings(self, base_colors):
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        center_x, center_y = self._get_body_center()
        energy = self.motion_level

        num_layers = 8
        max_radius = min(self.width, self.height) * 0.55 * (0.7 + 0.7 * self.render_scale)

        for i in range(num_layers):
            t = i / max(1, num_layers - 1)
            radius = max_radius * (0.2 + 0.8 * t)

            if len(base_colors) == 1:
                color = base_colors[0]
            else:
                idx = int(t * (len(base_colors) - 1))
                next_idx = min(idx + 1, len(base_colors) - 1)
                local_t = (t * (len(base_colors) - 1)) - idx
                color = self._lerp_color(base_colors[idx], base_colors[next_idx], local_t)

            alpha = int(230 * (0.4 + 0.8 * (1.0 - t)) * (0.6 + 0.7 * energy))
            alpha = max(0, min(alpha, 255))
            rgba = (color[0], color[1], color[2], alpha)

            segments = 32
            arc_len = math.tau * 0.6
            base_angle = self.time * (0.5 + 1.0 * energy) + i * 0.4

            for j in range(segments):
                a1 = base_angle + (j / segments) * arc_len
                a2 = base_angle + ((j + 0.7) / segments) * arc_len

                x1 = center_x + math.cos(a1) * radius
                y1 = center_y + math.sin(a1) * radius * 0.8
                x2 = center_x + math.cos(a2) * radius
                y2 = center_y + math.sin(a2) * radius * 0.8

                line_width = int(3 * self.stroke_boost)
                pygame.draw.line(surface, rgba, (int(x1), int(y1)), (int(x2), int(y2)), line_width)

        self.screen.blit(surface, (0, 0))

    # ------------------------------------------------------------------
    def _blit_camera(self, frame):
        try:
            h, w = frame.shape[:2]
        except Exception:
            return
    
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb = cv2.convertScaleAbs(frame_rgb, alpha=0.6, beta=0)  
    
        scale = min(self.width / w, self.height / h)
        new_size = (int(w * scale), int(h * scale))
        frame_resized = cv2.resize(frame_rgb, new_size)
    
        surf = pygame.surfarray.make_surface(frame_resized.swapaxes(0, 1))
        surf.set_alpha(60)  
        x = (self.width - new_size[0]) // 2
        y = (self.height - new_size[1]) // 2
        self.screen.blit(surf, (x, y))



    # ------------------------------------------------------------------
    def _draw_label(self):
        font = pygame.font.SysFont("arial", 26)
        title = f"Energy Field: {self.spectrum_name}"
        text = font.render(title, True, (245, 245, 245))
        self.screen.blit(text, (20, 18))

        if self.current_profile:
            elements_str = " · ".join(self.current_profile)
        elif self.current_element:
            elements_str = self.current_element
        else:
            elements_str = "None"

        sub_font = pygame.font.SysFont("arial", 22)
        profile_text = sub_font.render(
            f"Elements: {elements_str}", True, (230, 230, 230)
        )
        self.screen.blit(profile_text, (20, 50))

        # energy debug
        debug_font = pygame.font.SysFont("arial", 16)
        motion_text = debug_font.render(
            f"Energy(cam): {self.motion_level:.2f}", True, (220, 220, 220)
        )
        self.screen.blit(motion_text, (20, 80))

    # ------------------------------------------------------------------
    def _lerp_color(self, c1, c2, t):
        t = max(0.0, min(1.0, t))
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )

    def _boost_color(self, color, factor=2):
        r, g, b = color
        r = min(int(r * factor), 255)
        g = min(int(g * factor), 255)
        b = min(int(b * factor), 255)
        return (r, g, b)

    # ------------------------------------------------------------------
    def reset_profile(self):
        self.current_profile = None
        self.current_element = None
        self.spectrum_name = "None"
        self.style = get_spectrum_style([])  # back to neutral style
        self._clear_dynamic_buffers()
        self.scale = 1.0
        self.temp_shift = 0.0
        print("[Animation] Profile cleared. Waiting for new selection.")

    def get_frame_surface(self):
        surface = pygame.display.get_surface()
        if surface is None:
            return None
        return pygame.surfarray.array3d(surface)






