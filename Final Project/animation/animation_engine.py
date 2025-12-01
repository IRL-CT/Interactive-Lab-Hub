import pygame
import random
import math
import numpy as np

class AnimationEngine:
    def __init__(self, width=1280, height=720):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Inner Constellation")
        self.clock = pygame.time.Clock()

        self.current_element = None
        self.scale = 1.0
        self.temp_shift = 0.0
        self.particles = []

        # define simple base colors per element
        self.colors = {
            "Fire": [(255, 100, 50), (255, 200, 80)],
            "Water": [(50, 150, 255), (100, 220, 255)],
            "Wind": [(200, 240, 255), (150, 200, 255)],
            "Earth": [(100, 180, 100), (180, 240, 160)],
            "Light": [(255, 255, 255), (255, 240, 200)],
            "Shadow": [(80, 60, 120), (50, 30, 100)],
        }

    def update(self, element=None, gesture=None, frame=None):
        """
        Called every frame from main.py
        element: string name of current selected element
        gesture: dict or string describing movement
        frame: optional camera frame (OpenCV image)
        """
        # ---- handle user input ----
        if element and element != self.current_element:
            self.current_element = element
            self.particles.clear()
            print(f"[Engine] Element changed → {element}")

        if gesture:
            # interpret gestures
            if gesture == "up":
                self.scale = min(3.0, self.scale + 0.1)
            elif gesture == "down":
                self.scale = max(0.5, self.scale - 0.1)
            elif gesture == "left":
                self.temp_shift = max(-1.0, self.temp_shift - 0.05)
            elif gesture == "right":
                self.temp_shift = min(1.0, self.temp_shift + 0.05)

        # ---- draw frame ----
        self._draw_particles(element or self.current_element)

        pygame.display.flip()
        self.clock.tick(60)

    def _draw_particles(self, element):
        if not element:
            self.screen.fill((0, 0, 0))
            return

        # get colors
        c1, c2 = self.colors.get(element, [(255, 255, 255), (255, 255, 255)])

        # mix color temperature (colder = blue, warmer = orange)
        warm = (255, 180, 80)
        cold = (80, 160, 255)
        mix = self._lerp_color(cold, warm, (self.temp_shift + 1) / 2)
        bg = self._lerp_color((0, 0, 0), mix, 0.1)
        self.screen.fill(bg)

        # spawn new particles
        while len(self.particles) < int(200 * self.scale):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            vx = random.uniform(-1, 1)
            vy = random.uniform(-1, 1)
            life = random.uniform(2, 5)
            self.particles.append([x, y, vx, vy, life, random.choice([c1, c2])])

        # draw and update particles
        new_particles = []
        for p in self.particles:
            x, y, vx, vy, life, color = p
            life -= 0.03
            if life > 0:
                x += vx * 3 * self.scale
                y += vy * 3 * self.scale
                r = max(1, int(3 * self.scale))
                pygame.draw.circle(self.screen, color, (int(x), int(y)), r)
                new_particles.append([x, y, vx, vy, life, color])
        self.particles = new_particles

    def _lerp_color(self, c1, c2, t):
        t = max(0, min(1, t))
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )
