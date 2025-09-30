import random
import pygame
import os
import numpy as np
import matplotlib.pyplot as plt
from pygame.locals import *


class App:
    def __init__(self, width=920, height=610, caption="CRACKMe.exe"):
        """
        Sample App
        Args:
            width: очевидно
            height: нетрудно догадаться
            caption: оставим читателю, как упражнение

        :return: 😂😂😂
        """
        pygame.init()
        self.width, self.height = width, height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(caption)

        # Цвета
        self.colors = {
            'background': (40, 44, 52),
            'panel': (30, 34, 42),
            'text': (220, 220, 220),
            'border': (80, 85, 95),
            'highlight': (97, 175, 239),
            'button': (150, 150, 250),
            'draw_area' : (255, 255, 255),
            'draw_point_default' : (0, 0, 0),
        }

        # Шрифты
        self.font_large = pygame.font.Font(None, 32)
        self.font_medium = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)

        # Позиции и размеры
        self.margin = 20
        self.buttons_panel_width = 70
        self.buttons_panel_height = 30
        self.panel_width = self.width - 2 * self.margin
        self.panel_height = self.height - self.buttons_panel_height - 3 * self.margin

        self.button_prev = pygame.Rect(
            self.margin,
            self.margin,
            self.buttons_panel_width * 0.5 - 5,
            self.buttons_panel_height
        )
        self.button_next = pygame.Rect(
            self.margin + self.buttons_panel_width * 0.5 + 5,
            self.margin,
            self.buttons_panel_width * 0.5 - 5,
            self.buttons_panel_height
        )

        # Размеры миниатюр изображений
        self.thumb_width = 200
        self.thumb_height = 200

        # Флаги состояния
        self.running = False

        self.init_draw_area()
        self.init_draw_points()

    def init_draw_area(self):
        self.draw_area_border = pygame.Rect(
            self.margin,
            self.margin * 3,
            self.panel_width,
            self.panel_height
        )
        self.draw_area = pygame.Rect(
            self.margin + self.margin // 8,
            self.margin * 3 + self.margin // 8,
            self.panel_width - 2 * self.margin // 8,
            self.panel_height - 2 * self.margin // 8
        )

    def init_draw_points(self):
        if self.draw_area is None:
            return

        self.max_draw_point_count = 3
        self.draw_points = []
        self.draw_point_radius = 12

    def draw_point(self, pnt):
        if len(self.draw_points) < self.max_draw_point_count:
            self.draw_points.append(pnt)

    def draw_interface(self):
        """
        Отрисовка интерфейса
        """
        # Очищаем экран
        self.screen.fill(self.colors['background'])

        # Рисуем кнопки:
        pygame.draw.rect(self.screen, self.colors['button'], self.button_prev, border_radius=8)
        text = "<"
        text_surf = self.font_large.render(text, True, self.colors['text'])
        self.screen.blit(text_surf, (self.button_prev.x + 8, self.button_prev.y + 2))

        pygame.draw.rect(self.screen, self.colors['button'], self.button_next, border_radius=8)
        text = ">"
        text_surf = self.font_large.render(text, True, self.colors['text'])
        self.screen.blit(text_surf, (self.button_next.x + 10, self.button_next.y + 2))

        # Рисуем рамки областей
        if self.draw_area:
            pygame.draw.rect(self.screen, self.colors['border'], self.draw_area_border, 2)
            pygame.draw.rect(self.screen, self.colors['draw_area'], self.draw_area)
            if self.draw_points:
                for pnt in self.draw_points:
                    pygame.draw.circle(self.screen, self.colors['draw_point_default'], (pnt[0], pnt[1]), self.draw_point_radius)

    def collide(self, point, collision_box):
        x_col = (collision_box.x <= point[0]) and (collision_box.x + collision_box.width >= point[0])
        y_col = (collision_box.y <= point[1]) and (collision_box.y + collision_box.height >= point[1])
        return x_col and y_col

    def handle_events(self):
        """
        Обработка событий
        """
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False

            elif event.type == MOUSEBUTTONDOWN:
                if self.collide(event.pos, self.draw_area):
                    self.draw_point(event.pos)
                elif self.collide(event.pos, self.button_next):
                    continue

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                elif event.key == K_LEFT:
                    continue
                elif event.key == K_RIGHT:
                    continue


    def main_loop(self):
        """
        Главный цикл приложения
        """

        self.running = True
        clock = pygame.time.Clock()

        while self.running:
            self.handle_events()
            self.draw_interface()  # Добавили отрисовку!
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()


if __name__ == '__main__':
    app = App()
    app.main_loop()