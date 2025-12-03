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

        # Time and motion
        self.time = 0.0
        self.motion_level = 0.0              # 0~1, estimated from camera motion

        # Camera motion analysis
        self.prev_gray = None
        self.body_box = None                 # (x_min, y_min, x_max, y_max) in low-res space
        self.downsample_size = (64, 36)      # width, height for motion detection

        # Particle list: [x, y, vx, vy, life, base_color]
        self.particles = []

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
            self.particles.clear()  # reset particles for a clean transition
            print(f"[Animation] Spectrum profile -> {self.spectrum_name}")

        if self.current_profile is None and element and element != self.current_element:
            self.current_element = element
            self.spectrum_name = element
            self.particles.clear()
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

        # 3) Time and motion update
        dt_ms = self.clock.get_time()
        dt = dt_ms / 1000.0 if dt_ms > 0 else 1.0 / 60.0
        self.time += dt

        # Analyze motion if camera is available
        if frame is not None and cv2 is not None and np is not None:
            self._analyze_motion(frame)

        # Breathing modulation:
        # - motion_level increases cloud size
        # - sine wave adds organic breathing
        breath_from_motion = 1.0 + 0.6 * self.motion_level
        breathing_wave = 1.0 + 0.2 * math.sin(self.time * 2.0 * math.pi * 0.5)

        # Slowly decay scale back to normal range
        self.scale *= 0.99
        self.scale = max(0.6, min(2.5, self.scale))

        # Effective scale used for drawing / particle radius
        self.render_scale = self.scale * breath_from_motion * breathing_wave

        # Draw frame
        self._draw_frame(frame, dt)

        pygame.display.flip()
        self.clock.tick(60)

    # ------------------------------------------------------------------
    # Analyze camera motion and estimate a rough body center
    # ------------------------------------------------------------------
    def _analyze_motion(self, frame):
        # Convert to grayscale and downsample
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
        self.motion_level = 0.8 * self.motion_level + 0.2 * min(1.0, mean_diff * 8.0)

        # Threshold for active motion pixels
        _, diff_bin = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        ys, xs = np.where(diff_bin > 0)

        if len(xs) < 20:
            # Not enough motion → no reliable body box
            self.body_box = None
            return

        x_min, x_max = xs.min(), xs.max()
        y_min, y_max = ys.min(), ys.max()
        self.body_box = (x_min, y_min, x_max, y_max)

    # ------------------------------------------------------------------
    def _draw_frame(self, frame, dt):
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
        bg = self._lerp_color((0, 0, 0), tint, 0.08)
        self.screen.fill(bg)

        # 3) Draw camera behind particles
        if frame is not None and cv2 is not None:
            self._blit_camera(frame)

        # 4) Particle cloud around user's body center
        center_x, center_y = self._get_center()
        self._update_and_draw_particles(base_colors, center_x, center_y, dt)

        # 5) UI label
        self._draw_label()

    # ------------------------------------------------------------------
    # Decide where the particle cloud should be centered
    # ------------------------------------------------------------------
    def _get_center(self):
        if self.body_box is not None:
            x_min, y_min, x_max, y_max = self.body_box

            # Map from low-res motion space to screen coordinates
            scale_x = self.width / self.downsample_size[0]
            scale_y = self.height / self.downsample_size[1]

            cx = int((x_min + x_max) / 2 * scale_x)
            cy = int((y_min + y_max) / 2 * scale_y)

            # Clamp to screen bounds
            cx = max(0, min(self.width, cx))
            cy = max(0, min(self.height, cy))
            return cx, cy

        # Fallback: center of the screen
        return self.width // 2, self.height // 2

    # ------------------------------------------------------------------
    # Build a color palette from a 3-element profile
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

        cold_tint = self._lerp_color(avg, (80, 150, 255), 0.35)
        warm_tint = self._lerp_color(avg, (255, 200, 120), 0.35)

        return [cold_tint, avg, warm_tint]

    # ------------------------------------------------------------------
    # Spawn / update / draw particles near the body center
    # ------------------------------------------------------------------
    def _update_and_draw_particles(self, base_colors, cx, cy, dt):
        # Target particle count grows with render_scale
        target_count = int(260 * self.render_scale)
        target_count = max(120, min(target_count, 600))

        # Spawn new particles around the center
        while len(self.particles) < target_count:
            angle = random.uniform(0, math.tau)
            # Spread radius around the body, scaled by render_scale
            max_radius = 200 * self.render_scale
            r = random.uniform(0, max_radius)
            x = cx + math.cos(angle) * r
            y = cy + math.sin(angle) * r

            # Initial tangential swirl velocity
            speed = random.uniform(20, 60) * self.render_scale
            vx = -math.sin(angle) * speed
            vy = math.cos(angle) * speed

            life = random.uniform(1.5, 4.0)
            color = random.choice(base_colors)
            self.particles.append([x, y, vx, vy, life, color])

        new_particles = []
        for x, y, vx, vy, life, color in self.particles:
            life -= dt
            if life <= 0:
                continue

            # Vector from center to particle
            dx = x - cx
            dy = y - cy
            dist = math.hypot(dx, dy) + 1e-5

            # Gentle attraction back to the center
            # Stronger if particle is far away
            max_radius = 240 * self.render_scale
            pull_strength = 40.0 * (dist / max_radius)
            pull_strength = min(pull_strength, 80.0)

            ax = -dx / dist * pull_strength
            ay = -dy / dist * pull_strength

            # Slight swirl around the center
            swirl_strength = 30.0
            ax += -dy / dist * swirl_strength
            ay += dx / dist * swirl_strength

            # Integrate velocity and position
            vx += ax * dt
            vy += ay * dt
            x += vx * dt
            y += vy * dt

            # If particle goes very far off-screen, discard it early
            if x < -200 or x > self.width + 200 or y < -200 or y > self.height + 200:
                continue

            # Tint color slightly towards global temperature tint
            warm = (255, 180, 80)
            cold = (80, 150, 255)
            temp_tint = self._lerp_color(cold, warm, (self.temp_shift + 1) / 2)
            final_color = self._lerp_color(color, temp_tint, 0.25)

            # Particle size linked to distance from center and render_scale
            base_radius = 4.0 * self.render_scale
            radius = int(max(2, min(base_radius * (1.2 - 0.6 * (dist / max_radius)), 12)))

            pygame.draw.circle(self.screen, final_color, (int(x), int(y)), radius)
            new_particles.append([x, y, vx, vy, life, color])

        self.particles = new_particles

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
        surf.set_alpha(110)  # semi-transparent so particles stand out
        x = (self.width - new_size[0]) // 2
        y = (self.height - new_size[1]) // 2
        self.screen.blit(surf, (x, y))

    # ------------------------------------------------------------------
    def _draw_label(self):
        font = pygame.font.SysFont("arial", 24)
        text = font.render(f"Spectrum: {self.spectrum_name}", True, (230, 230, 230))
        self.screen.blit(text, (20, 20))

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
