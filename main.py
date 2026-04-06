import pygame
import sys

pygame.init()
pygame.font.init()

from config import WIDTH, HEIGHT, FPS
from simulation import Simulation

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mô Phỏng Tối Ưu Đèn Giao Thông - Pygame")
CLOCK = pygame.time.Clock()


def main():
    sim = Simulation()
    running = True

    while running:
        dt = CLOCK.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            sim.handle_input(event)

        sim.update(dt)
        sim.draw(SCREEN)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
