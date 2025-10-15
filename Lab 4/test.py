import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption("Pygame Window Test")

# Fill screen with light gray
screen.fill((200, 200, 200))
pygame.display.flip()

print("✅ Window opened successfully! Close it to end.")

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
sys.exit()
