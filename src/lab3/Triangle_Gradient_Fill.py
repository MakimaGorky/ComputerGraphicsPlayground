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
            'draw_area': (255, 255, 255),
            'draw_point_default': (0, 0, 0),
            'point_outline': (70, 70, 70)  # Тёмно-серый цвет для обводки
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

        # Для перетаскивания точек
        self.dragging_point_index = -1
        self.offset_x = 0
        self.offset_y = 0

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
        self.draw_point_radius = 8

    def draw_point(self, pnt):
        if len(self.draw_points) < self.max_draw_point_count:
            self.draw_points.append(
                (list(pnt),  # Храним точку как изменяемый список [x, y]
                 (random.randint(0, 255),
                  random.randint(0, 255),
                  random.randint(0, 255)
                  )
                 )
            )

    def draw_triangle(self):
        if len(self.draw_points) != 3:
            return

        # find square
        min_x = min([e[0][0] for e in self.draw_points])
        max_x = max([e[0][0] for e in self.draw_points])

        min_y = min([e[0][1] for e in self.draw_points])
        max_y = max([e[0][1] for e in self.draw_points])

        def edge_function(a, b, c):
            return (c[0] - a[0]) * (b[1] - a[1]) - (c[1] - a[1]) * (b[0] - a[0])

        A, A_col = self.draw_points[0]
        B, B_col = self.draw_points[1]
        C, C_col = self.draw_points[2]

        area2 = edge_function(A, B, C)

        if abs(area2) < 0.001:
            return

        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                pxl_mid = (x + 0.5, y + 0.5)

                # Использование барицентрических координат
                # Относительно A, B, C
                lambda_a = edge_function(B, C, pxl_mid) / area2
                lambda_b = edge_function(C, A, pxl_mid) / area2
                lambda_c = edge_function(A, B, pxl_mid) / area2

                if lambda_a >= 0 and lambda_b >= 0 and lambda_c >= 0:
                    pxl_r = int(max(0, min(lambda_a * A_col[0] + lambda_b * B_col[0] + lambda_c * C_col[0], 255)))
                    pxl_g = int(max(0, min(lambda_a * A_col[1] + lambda_b * B_col[1] + lambda_c * C_col[1], 255)))
                    pxl_b = int(max(0, min(lambda_a * A_col[2] + lambda_b * B_col[2] + lambda_c * C_col[2], 255)))

                    pygame.draw.circle(self.screen, (pxl_r, pxl_g, pxl_b), (x, y), 1)

    def draw_interface(self):
        """
        Отрисовка интерфейса
        """
        # Очищаем экран
        self.screen.fill(self.colors['background'])

        pygame.draw.rect(self.screen, self.colors['button'], self.button_prev, border_radius=8)
        text = "Х"
        text_surf = self.font_large.render(text, True, self.colors['text'])
        self.screen.blit(text_surf, (self.button_prev.x + 8, self.button_prev.y + 4))

        pygame.draw.rect(self.screen, self.colors['button'], self.button_next, border_radius=8)
        text = "<"
        text_surf = self.font_large.render(text, True, self.colors['text'])
        self.screen.blit(text_surf, (self.button_next.x + 8, self.button_next.y + 4))

        # Рисуем рамки областей
        if self.draw_area:
            pygame.draw.rect(self.screen, self.colors['border'], self.draw_area_border, 2)
            pygame.draw.rect(self.screen, self.colors['draw_area'], self.draw_area)

            if len(self.draw_points) == 3:
                self.draw_triangle()

            if self.draw_points:
                for pnt_index, (pnt_coords, pnt_color) in enumerate(self.draw_points):
                    # Рисуем обводку
                    pygame.draw.circle(self.screen, self.colors['point_outline'], (pnt_coords[0], pnt_coords[1]),
                                       self.draw_point_radius + 2)
                    # Рисуем саму точку
                    pygame.draw.circle(self.screen, pnt_color, (pnt_coords[0], pnt_coords[1]), self.draw_point_radius)

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
                if event.button == 1:  # Левая кнопка мыши
                    if self.collide(event.pos, self.draw_area):
                        # Проверяем, попали ли мы в существующую точку
                        for i, (pnt_coords, _) in enumerate(self.draw_points):
                            dist = ((event.pos[0] - pnt_coords[0]) ** 2 + (event.pos[1] - pnt_coords[1]) ** 2) ** 0.5
                            if dist < self.draw_point_radius + 2:  # Учитываем обводку для захвата
                                self.dragging_point_index = i
                                self.offset_x = pnt_coords[0] - event.pos[0]
                                self.offset_y = pnt_coords[1] - event.pos[1]
                                break
                        else:  # Если не попали в существующую точку, создаём новую
                            self.draw_point(event.pos)
                    elif self.collide(event.pos, self.button_prev):
                        self.draw_points = []
                    elif self.collide(event.pos, self.button_next):
                        self.draw_points = self.draw_points[:-1]

            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    self.dragging_point_index = -1  # Отпускаем точку

            elif event.type == MOUSEMOTION:
                if self.dragging_point_index != -1:
                    new_x = event.pos[0] + self.offset_x
                    new_y = event.pos[1] + self.offset_y

                    # Ограничиваем перемещение точкой в пределах draw_area
                    new_x = max(self.draw_area.left, min(new_x, self.draw_area.right))
                    new_y = max(self.draw_area.top, min(new_y, self.draw_area.bottom))

                    self.draw_points[self.dragging_point_index][0][0] = new_x
                    self.draw_points[self.dragging_point_index][0][1] = new_y

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                elif event.key == K_LEFT:
                    self.draw_points = self.draw_points[:-1]
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