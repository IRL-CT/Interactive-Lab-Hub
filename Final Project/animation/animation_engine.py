import pygame
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

        # Time and motion state (for breathing and aura response)
        self.time = 0.0
        self.motion_level = 0.0              # 0~1, estimated from camera motion

        # Camera motion analysis
        self.prev_gray = None
        self.body_box = None                 # (x_min, y_min, x_max, y_max) in low-res space
        self.downsample_size = (64, 36)      # width, height for motion detection

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
    # profile: ["Fire","Water","Light"] or None
    # element: "Fire", "Water", ... (used before profile is ready)
    # ------------------------------------------------------------------
    def update(self, profile=None, element=None, gesture=None, frame=None):
        # Handle Pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

        # 1) Handle element / profile changes
        # Priority: 3-element profile > single element
        if profile is not None and profile != self.current_profile:
            self.current_profile = profile
            self.current_element = None
            self.spectrum_name = " + ".join(profile)
            print(f"[Animation] Spectrum profile -> {self.spectrum_name}")

        if self.current_profile is None and element and element != self.current_element:
            self.current_element = element
            self.spectrum_name = element
            print(f"[Animation] Element -> {element}")

        # 2) Handle gesture input
        if gesture:
            if gesture == "expand":
                self.scale = min(3.0, self.scale + 0.1)
            elif gesture == "shrink":
                self.scale = max(0.5, self.scale - 0.1)
            elif gesture == "cooler":
                self.temp_shift = max(-1.0, self.temp_shift - 0.05)
            elif gesture == "warmer":
                self.temp_shift = min(1.0, self.temp_shift + 0.05)

        # 3) Time / breathing update
        dt_ms = self.clock.get_time()
        dt = dt_ms / 1000.0 if dt_ms > 0 else 1.0 / 60.0
        self.time += dt

        # Analyze motion if camera and numpy are available
        if frame is not None and cv2 is not None and np is not None:
            self._analyze_motion(frame)

        # Breathing modulation:
        # - motion_level increases breathing width/intensity
        # - sine wave adds slow organic oscillation
        breath_from_motion = 0.9 + 0.5 * self.motion_level
        breathing_wave = 1.0 + 0.15 * math.sin(self.time * 2.0 * math.pi * 0.5)

        # Slowly decay scale back to normal range
        self.scale *= 0.99
        self.scale = max(0.6, min(2.5, self.scale))

        # Effective scale used for drawing
        self.render_scale = self.scale * breath_from_motion * breathing_wave

        # Draw frame
        self._draw_frame(frame)

        pygame.display.flip()
        self.clock.tick(60)

    # ------------------------------------------------------------------
    # Analyze camera motion and estimate a rough body bounding box
    # ------------------------------------------------------------------
    def _analyze_motion(self, frame):
        # Convert to grayscale and downsample to a small resolution
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_small = cv2.resize(gray, self.downsample_size)

        if self.prev_gray is None:
            self.prev_gray = gray_small
            self.motion_level = 0.0
            self.body_box = None
            return

        # Frame difference
        diff = cv2.absdiff(gray_small, self.prev_gray)
        self.prev_gray = gray_small

        # Average intensity of difference (0~1)
        mean_diff = diff.mean() / 255.0
        # Smooth motion_level over time
        self.motion_level = 0.8 * self.motion_level + 0.2 * min(1.0, mean_diff * 6.0)

        # Estimate body box from thresholded motion map
        _, diff_bin = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        ys, xs = np.where(diff_bin > 0)

        if len(xs) < 30:
            # Not enough moving pixels → no reliable box
            self.body_box = None
            return

        x_min, x_max = xs.min(), xs.max()
        y_min, y_max = ys.min(), ys.max()
        self.body_box = (x_min, y_min, x_max, y_max)

    # ------------------------------------------------------------------
    def _draw_frame(self, frame):
        # 1) Determine base colors from profile or single element
        if self.current_profile is not None:
            base_colors = self._colors_from_profile(self.current_profile)
        else:
            element = self.current_element or "Shadow"
            base_colors = self.element_colors.get(
                element, [(255, 255, 255), (200, 200, 200)]
            )

        # 2) Background color based on temperature shift
        warm = (255, 180, 80)
        cold = (80, 150, 255)
        tint = self._lerp_color(cold, warm, (self.temp_shift + 1) / 2)
        bg = self._lerp_color((0, 0, 0), tint, 0.06)
        self.screen.fill(bg)

        # 3) Draw camera reflection behind aura
        if frame is not None and cv2 is not None:
            self._blit_camera(frame)

        # 4) Draw aura around the detected body region
        self._draw_aura(base_colors)

        # 5) UI label and debug info
        self._draw_label()

    # ------------------------------------------------------------------
    # Build a color palette from a 3-element profile
    # ------------------------------------------------------------------
    def _colors_from_profile(self, profile):
        # Collect all base colors from each element
        cols = []
        for name in profile:
            cols.extend(self.element_colors.get(name, []))

        if not cols:
            return [(255, 255, 255), (200, 200, 200)]

        # Average color across all contributing colors
        r = sum(c[0] for c in cols) // len(cols)
        g = sum(c[1] for c in cols) // len(cols)
        b = sum(c[2] for c in cols) // len(cols)
        avg = (r, g, b)

        # Create a simple gradient: cooler → avg → warmer
        cold_tint = self._lerp_color(avg, (80, 150, 255), 0.35)
        warm_tint = self._lerp_color(avg, (255, 200, 120), 0.35)

        return [cold_tint, avg, warm_tint]

    # ------------------------------------------------------------------
    # Draw a vertical energy aura around the body box (or center)
    # ------------------------------------------------------------------
    def _draw_aura(self, base_colors):
        """
        Draw a vertical energy aura (capsule-like column) using
        a separate alpha surface, then blit it onto the main screen.
        This should look like a strong glowing spectrum around the user.
        """

        aura_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Determine the center and vertical span of the aura
        if self.body_box is not None:
            x_min, y_min, x_max, y_max = self.body_box

            # Map from low-res motion space to screen coordinates
            scale_x = self.width / self.downsample_size[0]
            scale_y = self.height / self.downsample_size[1]

            cx = int((x_min + x_max) / 2 * scale_x)
            top = int(y_min * scale_y)
            bottom = int(y_max * scale_y)

            # Debug rectangle to show detected region (white box)
            debug_rect = pygame.Rect(
                int(x_min * scale_x),
                int(y_min * scale_y),
                int((x_max - x_min) * scale_x),
                int((y_max - y_min) * scale_y),
            )
            pygame.draw.rect(self.screen, (255, 255, 255), debug_rect, 2)

        else:
            # Fallback: central column when no body is detected
            cx = self.width // 2
            top = int(self.height * 0.2)
            bottom = int(self.height * 0.8)

        height = bottom - top
        if height < int(self.height * 0.25):
            # Ensure a minimum visible height
            top = int(self.height * 0.25)
            bottom = int(self.height * 0.75)
            height = bottom - top

        # Base column width influenced by scale and motion
        motion_factor = 1.0 + 0.8 * self.motion_level
        base_width = int(140 * self.render_scale * motion_factor)
        base_width = max(80, min(base_width, self.width // 2))

        # Rect describes the core of the column
        base_rect = pygame.Rect(0, 0, base_width, height)
        base_rect.centerx = cx
        base_rect.centery = (top + bottom) // 2

        # Slight vertical wobble over time to make the aura feel alive
        wobble = 18 * math.sin(self.time * 2.0 * math.pi * 0.3)
        base_rect.centery += int(wobble)

        # Draw multiple layered ellipses to form a glowing column
        num_layers = 16
        for i in range(num_layers):
            t = i / (num_layers - 1)

            # Color smoothly interpolates across the base palette
            if len(base_colors) == 1:
                color = base_colors[0]
            else:
                idx = int(t * (len(base_colors) - 1))
                next_idx = min(idx + 1, len(base_colors) - 1)
                segment_t = (t * (len(base_colors) - 1)) - idx
                color = self._lerp_color(base_colors[idx], base_colors[next_idx], segment_t)

            # Inner layers are brighter; outer layers more transparent
            alpha = int(255 * (1.0 - t ** 1.3))
            rgba = (color[0], color[1], color[2], alpha)

            # Inflate rect gradually to create soft edges
            inflate_x = int(base_width * 1.2 * t)
            inflate_y = int(height * 0.45 * t)
            layer_rect = base_rect.inflate(inflate_x, inflate_y)

            pygame.draw.ellipse(aura_surface, rgba, layer_rect)

        # Draw a bright core orb in the center
        core_radius = int(base_width * 0.6)
        core_radius = max(30, core_radius)
        core_color = base_colors[len(base_colors) // 2]
        core_rgba = (core_color[0], core_color[1], core_color[2], 255)
        core_center = (base_rect.centerx, base_rect.centery)
        pygame.draw.circle(aura_surface, core_rgba, core_center, core_radius)

        # Blit the aura on top of everything
        self.screen.blit(aura_surface, (0, 0))

    # ------------------------------------------------------------------
    def _blit_camera(self, frame):
        try:
            h, w = frame.shape[:2]
        except Exception:
            return

        # BGR -> RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Fit the camera frame into the screen while keeping aspect ratio
        scale = min(self.width / w, self.height / h)
        new_size = (int(w * scale), int(h * scale))
        frame_resized = cv2.resize(frame_rgb, new_size)

        surf = pygame.surfarray.make_surface(frame_resized.swapaxes(0, 1))
        surf.set_alpha(110)  # semi-transparent so aura stands out
        x = (self.width - new_size[0]) // 2
        y = (self.height - new_size[1]) // 2
        self.screen.blit(surf, (x, y))

    # ------------------------------------------------------------------
    def _draw_label(self):
        font = pygame.font.SysFont("arial", 24)
        text = font.render(f"Spectrum: {self.spectrum_name}", True, (230, 230, 230))
        self.screen.blit(text, (20, 20))

        # Debug: show motion level
        debug_font = pygame.font.SysFont("arial", 18)
        motion_text = debug_font.render(
            f"Motion: {self.motion_level:.2f}", True, (220, 220, 220)
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
