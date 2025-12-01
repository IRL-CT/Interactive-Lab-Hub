import pygame
import random
import math

class AnimationEngine:
    def __init__(self, width=1280, height=720):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Inner Constellation")
        self.clock = pygame.time.Clock()

        self.current_element = None
        self.scale = 1.0           # overall energy size
        self.temp_shift = 0.0      # -1.0 (cold) ~ +1.0 (warm)
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

    def update(self, element=None, gesture=None, frame=None):

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit


        if element and element != self.current_element:
            self.current_element = element
            self.particles.clear()
            print(f"[Animation] Element -> {element}")


        if gesture:
            if gesture == "expand":
                self.scale = min(3.0, self.scale + 0.1)
            elif gesture == "shrink":
                self.scale = max(0.5, self.scale - 0.1)
            elif gesture == "cooler":
                self.temp_shift = max(-1.0, self.temp_shift - 0.05)
            elif gesture == "warmer":
                self.temp_shift = min(1.0, self.temp_shift + 0.05)


        self._draw_frame()
        pygame.display.flip()
        self.clock.tick(60)

    def _draw_frame(self):
        element = self.current_element or "Shadow"  # 默认先给一个
        base_colors = self.element_colors.get(element, [(255, 255, 255), (200, 200, 200)])


        warm = (255, 180, 80)
        cold = (80, 150, 255)
        tint = self._lerp_color(cold, warm, (self.temp_shift + 1) / 2)
        bg = self._lerp_color((0, 0, 0), tint, 0.08)

        self.screen.fill(bg)


        target_count = int(180 * self.scale)
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

            # wrap around
            if x < -50: x = self.width + 50
            if x > self.width + 50: x = -50
            if y < -50: y = self.height + 50
            if y > self.height + 50: y = -50


            final_color = self._lerp_color(color, tint, 0.3)

            radius = max(1, int(3 * self.scale))
            pygame.draw.circle(self.screen, final_color, (int(x), int(y)), radius)

            new_particles.append([x, y, vx, vy, life, color])

        self.particles = new_particles


        self._draw_label(element)

    def _draw_label(self, element):
        font = pygame.font.SysFont("arial", 24)
        text = font.render(f"Element: {element}", True, (230, 230, 230))
        self.screen.blit(text, (20, 20))

    def _lerp_color(self, c1, c2, t):
        t = max(0.0, min(1.0, t))
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )
