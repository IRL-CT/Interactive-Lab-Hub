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

        # --------- 状态 ----------
        self.current_element = None          # 单一元素（fallback）
        self.current_profile = None          # 3 元素组合 ["Fire","Water","Light"]
        self.spectrum_name = "None"          # 用于 UI 的名字

        self.scale = 1.0          # energy size / breathing
        self.temp_shift = 0.0     # -1.0 (cold) ~ +1.0 (warm)
        self.particles = []

        # base colors per element
        self.element_colors = {
            "Fire":   [(255, 120, 60), (255, 200, 90)],
            "Water":  [(60, 140, 255), (110, 220, 255)],
            "Wind":   [(190, 230, 255), (150, 210, 255)],
            "Earth":  [(90, 160, 100), (170, 220, 150)],
            "Light":  [(255, 255, 255), (255, 240, 210)],
            "Shadow": [(120, 70, 160), (60, 30, 100)],
        }

        # 简单时间 & 运动量（给呼吸用，以后可以接摄像头）
        self.time = 0.0
        self.motion_level = 0.0   # 0~1

        # camera analysis
        self.prev_gray = None

    # --------------------------------------------------------
    #   profile: ["Fire","Water","Light"]  或 None
    #   element: "Fire" / "Water" ... 单元素 fallback
    # --------------------------------------------------------
    def update(self, profile=None, element=None, gesture=None, frame=None):
        # 处理 Pygame 事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

        # ---------- 1. 处理元素 / 组合 ----------
        # 优先使用 profile（三元素组合）
        if profile is not None and profile != self.current_profile:
            self.current_profile = profile
            self.current_element = None  # 不再用单元素
            self.particles.clear()

            self.spectrum_name = " + ".join(profile)
            print(f"[Animation] Spectrum profile -> {self.spectrum_name}")

        # 还没有 profile 的时候，继续用原来的单元素逻辑
        if self.current_profile is None and element and element != self.current_element:
            self.current_element = element
            self.spectrum_name = element
            self.particles.clear()
            print(f"[Animation] Element -> {element}")

        # ---------- 2. 手势调节 ----------
        if gesture:
            if gesture == "expand":
                self.scale = min(3.0, self.scale + 0.1)
            elif gesture == "shrink":
                self.scale = max(0.5, self.scale - 0.1)
            elif gesture == "cooler":
                self.temp_shift = max(-1.0, self.temp_shift - 0.05)
            elif gesture == "warmer":
                self.temp_shift = min(1.0, self.temp_shift + 0.05)

        # ---------- 3. 简单的“动作 → 呼吸”映射（基于摄像头运动量） ----------
        if frame is not None and cv2 is not None and np is not None:
            self._analyze_motion(frame)
            # 把 motion_level 映射到一个轻微呼吸变化（0.9~1.3）
            breath = 0.9 + 0.4 * self.motion_level
        else:
            breath = 1.0

        # 时间推进
        dt = self.clock.get_time() / 1000.0 if self.clock.get_time() > 0 else 1 / 60
        self.time += dt

        # 轻微的 sin 呼吸，让画面更有生命感
        breathing_wave = 1.0 + 0.1 * math.sin(self.time * 2 * math.pi * 0.5)  # 0.5Hz
        self.scale *= 0.98  # 慢慢回到原始大小（防止无限膨胀）
        self.scale = max(0.6, min(2.5, self.scale * breath * breathing_wave))

        # ---------- 4. 画一帧 ----------
        self._draw_frame(frame)
        pygame.display.flip()
        self.clock.tick(60)

    # --------------------------------------------------------
    #   分析摄像头运动：越动越大，motion_level 越接近 1
    # --------------------------------------------------------
    def _analyze_motion(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_small = cv2.resize(gray, (64, 36))

        if self.prev_gray is None:
            self.prev_gray = gray_small
            self.motion_level = 0.0
            return

        diff = cv2.absdiff(gray_small, self.prev_gray)
        self.prev_gray = gray_small

        # 平均差值归一化到 0~1
        mean_diff = diff.mean() / 255.0
        # 平滑一下
        self.motion_level = 0.8 * self.motion_level + 0.2 * min(1.0, mean_diff * 5.0)

    # --------------------------------------------------------
    def _draw_frame(self, frame):
        # 1）根据元素 / 组合获取颜色 palette
        if self.current_profile is not None:
            base_colors = self._colors_from_profile(self.current_profile)
        else:
            element = self.current_element or "Shadow"
            base_colors = self.element_colors.get(
                element, [(255, 255, 255), (200, 200, 200)]
            )

        # 背景色：由 temp_shift 和冷暖色插值
        warm = (255, 180, 80)
        cold = (80, 150, 255)
        tint = self._lerp_color(cold, warm, (self.temp_shift + 1) / 2)
        bg = self._lerp_color((0, 0, 0), tint, 0.05)

        self.screen.fill(bg)

        # 叠加摄像头画面
        if frame is not None and cv2 is not None:
            self._blit_camera(frame)

        # 粒子数量和 scale 相关
        target_count = int(220 * self.scale)
        while len(self.particles) < target_count:
            x = random.uniform(0, self.width)
            y = random.uniform(0, self.height)
            angle = random.uniform(0, math.tau)
            speed = random.uniform(20, 80) * self.scale
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life = random.uniform(2.0, 5.0)
            color = random.choice(base_colors)
            self.particles.append([x, y, vx, vy, life, color])

        new_particles = []
        for x, y, vx, vy, life, color in self.particles:
            life -= 0.03
            if life <= 0:
                continue

            x += vx * 0.03
            y += vy * 0.03

            # wrap around 四周
            if x < -50: x = self.width + 50
            if x > self.width + 50: x = -50
            if y < -50: y = self.height + 50
            if y > self.height + 50: y = -50

            final_color = self._lerp_color(color, tint, 0.3)
            radius = max(1, int(3 * self.scale))
            pygame.draw.circle(self.screen, final_color, (int(x), int(y)), radius)

            new_particles.append([x, y, vx, vy, life, color])

        self.particles = new_particles

        self._draw_label()

    # --------------------------------------------------------
    #   把三个元素的颜色混合成一套 palette
    # --------------------------------------------------------
    def _colors_from_profile(self, profile):
        # 获取三种元素的 base color 列表
        cols = []
        for name in profile:
            cols.extend(self.element_colors.get(name, []))

        if not cols:
            return [(255, 255, 255), (200, 200, 200)]

        # 取平均色作为中间色
        r = sum(c[0] for c in cols) // len(cols)
        g = sum(c[1] for c in cols) // len(cols)
        b = sum(c[2] for c in cols) // len(cols)
        avg = (r, g, b)

        # palette：偏冷 / 平均 / 偏暖
        cold_tint = self._lerp_color(avg, (80, 150, 255), 0.3)
        warm_tint = self._lerp_color(avg, (255, 200, 120), 0.3)

        return [cold_tint, avg, warm_tint]

    # --------------------------------------------------------
    def _blit_camera(self, frame):
        try:
            h, w = frame.shape[:2]
        except Exception:
            return

        # BGR -> RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        scale = min(self.width / w, self.height / h)
        new_size = (int(w * scale), int(h * scale))
        frame_resized = cv2.resize(frame_rgb, new_size)

        surf = pygame.surfarray.make_surface(frame_resized.swapaxes(0, 1))
        surf.set_alpha(120)
        x = (self.width - new_size[0]) // 2
        y = (self.height - new_size[1]) // 2
        self.screen.blit(surf, (x, y))

    # --------------------------------------------------------
    def _draw_label(self):
        font = pygame.font.SysFont("arial", 24)
        text = font.render(f"Spectrum: {self.spectrum_name}", True, (230, 230, 230))
        self.screen.blit(text, (20, 20))

    # --------------------------------------------------------
    def _lerp_color(self, c1, c2, t):
        t = max(0.0, min(1.0, t))
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )
