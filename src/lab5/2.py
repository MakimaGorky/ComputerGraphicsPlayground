
import pygame
import sys
from midpoint_displacement import MountainMirthMachine


WIDTH, HEIGHT = 800, 400
BASE_POINTS = [(0, HEIGHT // 2), (WIDTH, HEIGHT // 2)]
FPS = 30

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
SKY = (100, 150, 255)
GROUND = (50, 200, 50)
LINE = (0, 0, 0)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Midpoint Displacement")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)


def draw_mountains(surface, points):
    pygame.draw.polygon(surface, GROUND, points + [(WIDTH, HEIGHT), (0, HEIGHT)])
    pygame.draw.lines(surface, LINE, False, points, 2)


if __name__ == "__main__":
    MMM = MountainMirthMachine(BASE_POINTS)
    step = 1

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Управление параметрами
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    MMM.displacement += 10
                elif event.key == pygame.K_DOWN:
                    MMM.displacement = max(10, INITIAL_DISPLACEMENT - 10)
                elif event.key == pygame.K_SPACE:
                    step += 1
                elif event.key == pygame.K_z:
                    step = max(1, step - 1)
                elif event.key == pygame.K_RIGHT:
                    MMM.roughness = min(0.99, MMM.roughness + 0.05)
                elif event.key == pygame.K_LEFT:
                    MMM.roughness = max(0.1, MMM.roughness - 0.05)
                elif event.key == pygame.K_ESCAPE:
                    step = 1
                    MMM = MountainMirthMachine(BASE_POINTS)

        screen.fill(SKY)

        # Рисуем текущий шаг
        draw_mountains(screen, MMM.get_state(step))

        # Текст
        info = [
            f"Итерация: {step}",
            f"Амплитуда: {MMM.current_displacement(step)}",
            f"Roughness: {MMM.roughness:.2f}",
            "Exc — сброс | Стрелки — параметры | Пробел, Z — управление"
        ]
        for i, t in enumerate(info):
            screen.blit(font.render(t, True, BLACK), (10, 10 + i * 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()