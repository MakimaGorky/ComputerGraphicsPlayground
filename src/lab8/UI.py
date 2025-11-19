import pygame
from primitives import *


class WindowInfo:
    def __init__(self):
        self.width = 0
        self.height = 0
        self.center = Vector2()


class ObjectOption:
    def __init__(self, name: str, creator):
        self.name = name
        self.create = creator


def get_window_info(screen) -> WindowInfo:
    result = WindowInfo()
    info = pygame.display.Info()
    result.width = info.current_w
    result.height = info.current_h
    result.center.x = result.width / 2.0
    result.center.y = result.height / 2.0
    return result


def button(screen, font, rect: Rectangle, text: str) -> bool:
    mouse_pos = pygame.mouse.get_pos()

    is_hovered = (rect.x <= mouse_pos[0] <= rect.x + rect.width and
                  rect.y <= mouse_pos[1] <= rect.y + rect.height)

    color = (100, 100, 200) if is_hovered else (70, 70, 170)

    pygame.draw.rect(screen, color, (rect.x, rect.y, rect.width, rect.height))
    pygame.draw.rect(screen, (255, 255, 255), (rect.x, rect.y, rect.width, rect.height), 2)

    text_surface = font.render(text, True, (255, 255, 255))
    text_x = rect.x + (rect.width - text_surface.get_width()) / 2
    text_y = rect.y + (rect.height - text_surface.get_height()) / 2
    screen.blit(text_surface, (text_x, text_y))

    return is_hovered and pygame.mouse.get_pressed()[0]


def input_box(screen, font, rect: Rectangle, text: str, active: bool) -> str:
    mouse_pos = pygame.mouse.get_pos()
    is_hovered = (rect.x <= mouse_pos[0] <= rect.x + rect.width and
                  rect.y <= mouse_pos[1] <= rect.y + rect.height)

    color = (240, 240, 240) if active else (220, 220, 220)
    if is_hovered:
        color = (250, 250, 250)

    pygame.draw.rect(screen, color, (rect.x, rect.y, rect.width, rect.height))
    pygame.draw.rect(screen, (0, 0, 0), (rect.x, rect.y, rect.width, rect.height), 2)

    text_surface = font.render(text, True, (0, 0, 0))
    text_x = rect.x + 5
    text_y = rect.y + (rect.height - text_surface.get_height()) / 2
    screen.blit(text_surface, (text_x, text_y))

    return is_hovered and pygame.mouse.get_pressed()[0]

