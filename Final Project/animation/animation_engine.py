import pygame
import random
import math

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None


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

        # Energy scale and temperature
        self.scale = 1.0                     # base energy size (changed by gestures)
        self.temp_shift = 0.0                # -1.0 (cold) ~ +1.0 (warm)

        # Time and "motion energy"
        self.time = 0.0
        self.motion_level = 0.0              # 0~1, estimated from camera motion (global)

        # Camera motion analysis
        self.prev_gray = None
        self.downsample_size = (64, 36)      # for motion estimation

        # Orbiting energy orbs
        self.orbs = []                       # each: [radius, angle, speed, size, color_idx]

        # Base colors per element
        self.element_colors = {
            "Fire":   [(255, 120, 60), (255, 200, 90)],
            "Water":  [(60, 140, 255), (110, 220, 255)],
            "Wind":   [(190, 230, 255), (150, 210, 255)],
            "Earth":  [(90, 160, 100), (170, 220, 150)],
            "Light":  [(255, 255, 255), (255, 240, 210)],
            "Shadow": [(120, 70, 160), (60, 30, 100)],
        }

    # ------------------------------------------------------------------
    # Main update entry
    # profile: ["Fire","Water","Light"] or None
    # element: "Fire", "Water", ... (used before profile is ready)
    # frame: camera frame in BGR (OpenCV)
    # ------------------------------------------------------------------
    def update(self, profile=None, element=None, gesture=None, frame=None):
        # Handle Pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

        # 1) Handle element / profile changes
        if profile is not None and profile != self.current_profile:
            self.current_profile = profile
            self.current_element = None
            self.spectrum_name = " + ".join(profile)
            print(f"[Animation] Spectrum profile -> {self.spectrum_name}")

            # Reset orbs to introduce fresh layout for new combination
            self.orbs.clear()

        if self.current_profile is None and element and element != self.current_element:
            self.current_element = element
            self.spectrum_name = element
            print(f"[Animation] Element -> {element}")
            self.orbs.clear()

        # 2) Handle gesture input (optional physical control)
        if gesture:
            if gesture == "expand":
                self.scale = min(3.0, self.scale + 0.1)
            elif gesture == "shrink":
                self.scale = max(0.5, self.scale - 0.1)
            elif gesture == "cooler":
                self.temp_shift = max(-1.0, self.temp_shift - 0.05)
            elif gesture == "warmer":
                self.temp_shift = min(1.0, self.temp_shift + 0.05)

        # 3) Time update
        dt_ms = self.clock.get_time()
        dt = dt_ms / 1000.0 if dt_ms > 0 else 1.0 / 60.0
        self.time += dt

        # 4) Global motion energy from camera (no body outline, just "how alive" the scene is)
        if frame is not None and cv2 is not None and np is not None:
            self._update_motion_energy(frame)

        # 5) Breathing modulation:
        # motion_level controls overall intensity
        # sine wave makes it feel alive and slow-breathing
        breath_from_motion = 1.0 + 0.8 * self.motion_level
        breathing_wave = 1.0 + 0.18 * math.sin(self.time * 2.0 * math.pi * 0.4)

        # Slowly decay base scale back to normal
        self.scale *= 0.99
        self.scale = max(0.6, min(2.5, self.scale))

        # This is the effective scale for drawing
        self.render_scale = self.scale * breath_from_motion * breathing_wave

        # Draw frame
        self._draw_frame(frame, dt)

        pygame.display.flip()
        self.clock.tick(60)

    # ------------------------------------------------------------------
    # Compute a single "motion_level" from camera: how much the scene changes
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

        # Average difference gives a rough motion energy
        mean_diff = diff.mean() / 255.0
        self.motion_level = 0.85 * self.motion_level + 0.15 * min(1.0, mean_diff * 8.0)

    # ------------------------------------------------------------------
    def _draw_frame(self, frame, dt):
        # 1) Colors based on profile or single element
        if self.current_profile is not None:
            base_colors = self._colors_from_profile(self.current_profile)
        else:
            element = self.current_element or "Shadow"
            base_colors = self.element_colors.get(
                element, [(255, 255, 255), (200, 200, 200)]
            )

        # 2) Background gradient based on temperature shift
        warm = (255, 180, 80)
        cold = (80, 150, 255)
        temp_tint = self._lerp_color(cold, warm, (self.temp_shift + 1) / 2)
        bg = self._lerp_color((0, 0, 0), temp_tint, 0.12)
        self.screen.fill(bg)

        # 3) Camera reflection (very soft) behind everything
        if frame is not None and cv2 is not None:
            self._blit_camera(frame)

        # 4) Central energy aura (pillar + head halo)
        self._draw_aura(base_colors)

        # 5) Orbiting "element orbs" around the aura
        self._update_and_draw_orbs(base_colors, dt)

        # 6) Label
        self._draw_label()

    # ------------------------------------------------------------------
    # Blend element colors to build a "spectrum"
    # ------------------------------------------------------------------
    def _colors_from_profile(self, profile):
        cols = []
        for name in profile:
            cols.extend(self.element_colors.get(name, []))

        if not cols:
            return [(255, 255, 255), (200, 200, 200)]

        r = sum(c[0] for c in cols) // len(cols)
        g = sum(c[1] for c in cols) // len(cols)
        b = sum(c[2] for c in cols) // len(cols)
        avg = (r, g, b)

        # cooler, mid, warmer variants
        cold_tint = self._lerp_color(avg, (80, 150, 255), 0.35)
        warm_tint = self._lerp_color(avg, (255, 200, 120), 0.35)

        return [cold_tint, avg, warm_tint]

    # ------------------------------------------------------------------
    # Central aura: a vertical glowing pillar + a halo around "head" position
    # ------------------------------------------------------------------
    def _draw_aura(self, base_colors):
        """
        Draw a dream-like aura in the center of the screen:
        - A vertical gradient pillar (like a body)
        - A circular halo at the upper part (like a head aura)
        """

        aura_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        center_x = self.width // 2
        center_y = int(self.height * 0.55)  # body center
        pillar_height = int(self.height * 0.6 * self.render_scale)
        pillar_height = max(int(self.height * 0.4), min(pillar_height, int(self.height * 0.8)))

        top_y = center_y - pillar_height // 2
        bottom_y = center_y + pillar_height // 2

        # Pillar base width depends on render_scale
        base_width = int(140 * self.render_scale)
        base_width = max(80, min(base_width, self.width // 2))

        base_rect = pygame.Rect(0, 0, base_width, pillar_height)
        base_rect.centerx = center_x
        base_rect.centery = center_y

        # Slight vertical breathing wobble
        wobble = 12 * math.sin(self.time * 2.0 * math.pi * 0.3)
        base_rect.centery += int(wobble)

        # Draw multiple layered ellipses to form the pillar
        num_layers = 18
        for i in range(num_layers):
            t = i / (num_layers - 1)

            # Interpolate through the spectrum palette
            if len(base_colors) == 1:
                color = base_colors[0]
            else:
                idx = int(t * (len(base_colors) - 1))
                next_idx = min(idx + 1, len(base_colors) - 1)
                local_t = (t * (len(base_colors) - 1)) - idx
                color = self._lerp_color(base_colors[idx], base_colors[next_idx], local_t)

            # Alpha: bright in the center, softer outside
            alpha = int(255 * (1.0 - t ** 1.4))
            rgba = (color[0], color[1], color[2], alpha)

            # Horizontal inflation makes outer glow
            inflate_x = int(base_width * 1.4 * t)
            inflate_y = int(pillar_height * 0.4 * t)
            layer_rect = base_rect.inflate(inflate_x, inflate_y)

            pygame.draw.ellipse(aura_surface, rgba, layer_rect)

        # Head halo: circle above the center of the pillar
        head_y = base_rect.top + int(pillar_height * 0.18)
        halo_radius = int(base_width * 0.7)
        halo_radius = max(40, halo_radius)

        halo_center = (center_x, head_y)
        for i in range(8):
            t = i / 7.0
            color = base_colors[min(len(base_colors) - 1, i % len(base_colors))]
            alpha = int(220 * (1.0 - t ** 1.8))
            radius = int(halo_radius * (0.6 + 0.5 * t * self.render_scale))

            rgba = (color[0], color[1], color[2], alpha)
            pygame.draw.circle(aura_surface, rgba, halo_center, radius)

        # Core "soul" orb
        core_color = base_colors[len(base_colors) // 2]
        core_rgba = (core_color[0], core_color[1], core_color[2], 255)
        core_radius = int(base_width * 0.45)
        core_radius = max(30, core_radius)
        pygame.draw.circle(aura_surface, core_rgba, halo_center, core_radius)

        # Blend aura onto main screen
        self.screen.blit(aura_surface, (0, 0))

    # ------------------------------------------------------------------
    # Orbiting orbs around the aura (representing the 3 elements)
    # ------------------------------------------------------------------
    def _update_and_draw_orbs(self, base_colors, dt):
        """
        Draw small glowing orbs that orbit around the aura.
        Their speed and size are influenced by the motion energy.
        """

        center_x = self.width // 2
        center_y = int(self.height * 0.55)

        # Ensure we have a stable set of orbs
        desired_orb_count = 24
        if len(self.orbs) == 0:
            for i in range(desired_orb_count):
                # Radius layers: some near the body, some further out
                radius = random.uniform(120, 260)
                angle = random.uniform(0, math.tau)
                # Base speed influenced by motion_level
                speed = random.uniform(0.3, 0.9)
                size = random.uniform(4.0, 10.0)
                color_idx = random.randint(0, len(base_colors) - 1)
                self.orbs.append([radius, angle, speed, size, color_idx])
        elif len(self.orbs) < desired_orb_count:
            # Top up slowly if needed
            for i in range(desired_orb_count - len(self.orbs)):
                radius = random.uniform(120, 260)
                angle = random.uniform(0, math.tau)
                speed = random.uniform(0.3, 0.9)
                size = random.uniform(4.0, 10.0)
                color_idx = random.randint(0, len(base_colors) - 1)
                self.orbs.append([radius, angle, speed, size, color_idx])

        # Draw each orb
        for orb in self.orbs:
            radius, angle, speed, size, color_idx = orb

            # Orbital angular speed amplified by motion_level
            angular_speed = speed * (1.0 + 1.2 * self.motion_level)
            orb[1] += angular_speed * dt

            # Compute position
            x = center_x + math.cos(orb[1]) * radius
            y = center_y + math.sin(orb[1]) * radius * 0.55  # slightly squashed vertically

            # Size breathing with scene energy
            final_size = size * (0.8 + 0.6 * self.render_scale)
            final_size = max(2.0, min(final_size, 18.0))

            color = base_colors[color_idx]
            # Slight shimmering by mixing with temp tint
            warm = (255, 180, 80)
            cold = (80, 150, 255)
            temp_tint = self._lerp_color(cold, warm, (self.temp_shift + 1) / 2)
            final_color = self._lerp_color(color, temp_tint, 0.25)

            # Draw a soft glowing orb
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
        surf.set_alpha(90)  # very soft reflection
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
            f"Energy: {self.motion_level:.2f}", True, (220, 220, 220)
        )
        self.screen.blit(motion_text, (20, 50))

    # ------------------------------------------------------------------
    def _lerp_color(self, c1, c2, t):
        t = max(0.0, min(1.0, t))
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )
