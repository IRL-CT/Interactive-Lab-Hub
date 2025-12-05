# animation/animation_engine.py
#
# Camera-driven Inner Constellation (no gesture sensor).
# - Horizontal position (body_x) → color temperature of the ENERGY FIELD
# - Approximate distance (size_level) → size of the ENERGY FIELD
# - Field center follows motion centroid.

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

        # Style from set_profile
        self.style = get_spectrum_style([])

        # Energy scale and temperature
        self.scale = 1.0               # base energy size
        self.temp_shift = 0.0          # -1.0 (cold) ~ +1.0 (warm)

        # Time and camera-derived energy levels
        self.time = 0.0
        self.motion_level = 0.0        # 0~1, how much the user is moving

        # Camera motion analysis
        self.prev_gray = None
        self.downsample_size = (64, 36)

        # Approximate body position (0~1) from camera motion centroid
        self.body_x = 0.5   # 0 = left, 1 = right
        self.body_y = 0.5   # 0 = top, 1 = bottom

        # Approximate body size (0~1) from activated area in diff
        self.size_level = 0.0          # larger = closer

        # Persistent particles for some patterns
        self.orbs = []

        # Fallback colors
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
            gesture: ignored (gesture sensor disabled)
            proximity: ignored (no APDS-9960)
            frame: OpenCV camera frame (BGR) or None
        """
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

        # 2) Time step
        dt_ms = self.clock.get_time()
        dt = dt_ms / 1000.0 if dt_ms > 0 else 1.0 / 60.0
        self.time += dt

        # 3) Camera features: motion + position + approximate size
        if frame is not None and cv2 is not None and np is not None:
            self._update_motion_features(frame)

        # 4) body_x → temp_shift (-1 ~ +1)
        target_temp = (self.body_x - 0.5) * 2.0
        target_temp = max(-1.0, min(1.0, target_temp))
        self.temp_shift = 0.9 * self.temp_shift + 0.1 * target_temp

        # 5) size_level → scale
        base_scale = 1.5
        target_scale = base_scale + (0.9 - 1.6 * self.size_level)
        self.scale = 0.9 * self.scale + 0.1 * target_scale
        self.scale = max(0.6, min(3.0, self.scale))

        # 6) Breathing modulation
        breath_from_motion = 1.0 + 0.9 * self.motion_level
        breathing_wave = 1.0 + 0.28 * math.sin(self.time * 2.0 * math.pi * 0.4)
        self.render_scale = self.scale * breath_from_motion * breathing_wave

        # 7) Draw frame
        self._draw_frame(frame, dt)

        pygame.display.flip()
        self.clock.tick(60)

    # ------------------------------------------------------------------
    def _update_motion_features(self, frame):
        """Compute motion_level, body_x/body_y, and size_level from camera frames."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_small = cv2.resize(gray, self.downsample_size)

        if self.prev_gray is None:
            self.prev_gray = gray_small
            self.motion_level = 0.0
            self.size_level = 0.0
            return

        diff = cv2.absdiff(gray_small, self.prev_gray)
        self.prev_gray = gray_small

        # Global motion strength
        mean_diff = diff.mean() / 255.0
        self.motion_level = 0.85 * self.motion_level + 0.15 * min(1.0, mean_diff * 8.0)

        # Active region ratio → approximate size
        diff_norm = diff.astype("float32") / 255.0
        mask = diff_norm > 0.18
        active_ratio = mask.mean()
        size_raw = min(1.0, active_ratio * 18.0)
        self.size_level = 0.9 * self.size_level + 0.1 * size_raw

        # Motion centroid → body position
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
        """Map camera 0~1 body coordinates to screen coordinates with margin."""
        x = int(self.width * (0.15 + 0.7 * self.body_x))   # 15%~85% width
        y = int(self.height * (0.25 + 0.5 * self.body_y))  # 25%~75% height
        return x, y

    # ------------------------------------------------------------------
    def _draw_frame(self, frame, dt):
        # Base colors from style
        if self.current_profile is not None or self.current_element is not None:
            base_colors = self.style.get(
                "base_colors", [(255, 255, 255), (200, 200, 200)]
            )
        else:
            base_colors = [(255, 255, 255), (200, 200, 200)]

        # === Global temperature (based on horizontal position) ===
        # temp_shift: -1 (cold) ~ +1 (warm) → 0~1
        temp_t = (self.temp_shift + 1) / 2.0
        temp_t = max(0.0, min(1.0, temp_t))

        # A "pure" cold/warm reference
        cold_core = (80, 150, 255)
        warm_core = (255, 190, 100)
        tint_target = self._lerp_color(cold_core, warm_core, temp_t)

        # Background only slightly tinted (to keep focus on aura)
        bg = self._lerp_color((0, 0, 0), tint_target, 0.18)
        self.screen.fill(bg)

        # === Apply temperature tint to energy colors (STRONG) ===
        # We push each base color toward the tint_target so patterns change color clearly.
        tinted_colors = []
        for c in base_colors:
            # 0.0 keeps original, 1.0 = fully tint_target
            # 0.65 is a strong but not total override.
            tinted = self._lerp_color(c, tint_target, 0.65)
            tinted_colors.append(tinted)

        # Camera reflection
        if frame is not None and cv2 is not None:
            self._blit_camera(frame)

        # Pattern routing (using tinted_colors so energy actually changes color)
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
        else:
            self._pattern_pillar_orbs(tinted_colors, dt)

        self._draw_label()

    # ------------------------------------------------------------------
    # PATTERN 1: central pillar + orbiting orbs (following body)
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
    # PATTERN 2–10 (same as之前，只是用 base_colors 作为已经被tint过的颜色)
    # ------------------------------------------------------------------
    # 为了不太长，这里我保留你现有版本里其它 pattern 的实现逻辑，
    # 只要保证它们的第一个参数用的是 base_colors（现在已经是 tinted_colors）。
    # 你可以直接把你当前文件里 _pattern_ring_waves、_pattern_radial_rays、
    # _pattern_galaxy、_pattern_double_pillar、_pattern_vertical_ribbons、
    # _pattern_grid_pulse、_pattern_starfield、_pattern_vortex、_pattern_cross_waves
    # 原样贴到这里即可，无需修改内部颜色逻辑。

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

        debug_font = pygame.font.SysFont("arial", 16)
        motion_text = debug_font.render(
            f"Motion: {self.motion_level:.2f}", True, (220, 220, 220)
        )
        pos_text = debug_font.render(
            f"Position: x={self.body_x:.2f}, y={self.body_y:.2f}", True, (220, 220, 220)
        )
        size_text = debug_font.render(
            f"Size level: {self.size_level:.2f}", True, (220, 220, 220)
        )
        temp_text = debug_font.render(
            f"Temp shift: {self.temp_shift:.2f}", True, (220, 220, 220)
        )

        self.screen.blit(motion_text, (20, 80))
        self.screen.blit(pos_text, (20, 100))
        self.screen.blit(size_text, (20, 120))
        self.screen.blit(temp_text, (20, 140))

    # ------------------------------------------------------------------
    def _lerp_color(self, c1, c2, t):
        t = max(0.0, min(1.0, t))
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )

    def reset_profile(self):
        self.current_profile = None
        self.current_element = None
        self.spectrum_name = "None"
        self.style = get_spectrum_style([])
        self.orbs.clear()
        self.scale = 1.0
        self.temp_shift = 0.0
        print("[Animation] Profile cleared. Waiting for new selection.")
