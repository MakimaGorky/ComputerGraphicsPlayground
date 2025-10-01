"""
1в) Выделение границы связной области.
    Обход границы с занесением точек в список и прорисовкой поверх изображения.
"""
import numpy as np
import pygame as pg
import os
import sys
sys.path.append("libs")
from ImagesLoader import *


class BoundaryTracer:
    """
    Выделяет и обходит границу связной области с обнаружением отверстий
    """
    def __init__(self, screen, assets_path='coloring_pages'):
        self.images_loader = ImagesLoader(screen, assets_path)
        self.image = self.images_loader.get_image()
        self.width, self.height = self.image.get_size()
        self.screen = screen
        self.image_offset = (100, 100)
        self.have_clicked = False
        self.boundary_points = []
        self.boundary_color = (255, 0, 0)  # Красный цвет для отрисовки
        self.show_boundary = False

        # Направления обхода (8-связность): начиная с верха и по часовой
        self.directions = [
            (0, -1),
            (1, -1),
            (1, 0),
            (1, 1),
            (0, 1),
            (-1, 1),
            (-1, 0),
            (-1, -1)
        ]

    def is_boundary(self, x, y, target_color):
        """
        Проверяет, является ли точка границей (цвет отличается от целевого)
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return True  # За пределами - считаем границей
        return self.image.get_at((x, y))[:3] != target_color[:3]

    def trace_contour(self, start_x, start_y, target_color, visited):
        """
        Обходит контур начиная с точки (start_x, start_y)
        Использует алгоритм обхода границы
        """
        contour = []

        current_x, current_y = start_x, start_y

        # Проверяем, что текущая точка внутри области
        if self.is_boundary(current_x, current_y, target_color):
            return contour

        boundary_start = None
        for dx, dy in self.directions:
            nx, ny = current_x + dx, current_y + dy
            if self.is_boundary(nx, ny, target_color):
                boundary_start = (current_x, current_y)
                break

        if not boundary_start:
            return contour

        current_x, current_y = boundary_start
        start_point = boundary_start

        visited_set = set()
        max_iterations = self.width * self.height
        iterations = 0

        # Обход по периметру
        prev_dir = 0

        while iterations < max_iterations:
            iterations += 1

            if (current_x, current_y) not in visited_set:
                contour.append((current_x, current_y))
                visited.add((current_x, current_y))
                visited_set.add((current_x, current_y))

            found = False
            # Начинаем поиск с направления, перпендикулярного предыдущему движению
            start_dir = (prev_dir + 6) % 8  # Поворот налево

            for i in range(8):
                check_dir = (start_dir + i) % 8
                dx, dy = self.directions[check_dir]
                next_x, next_y = current_x + dx, current_y + dy

                # Проверяем, что точка внутри области (не граница)
                if not self.is_boundary(next_x, next_y, target_color):
                    # Проверяем, что рядом есть граница
                    has_boundary_neighbor = False
                    for dx2, dy2 in self.directions:
                        if self.is_boundary(next_x + dx2, next_y + dy2, target_color):
                            has_boundary_neighbor = True
                            break

                    if has_boundary_neighbor:
                        current_x, current_y = next_x, next_y
                        prev_dir = check_dir
                        found = True

                        # Проверяем замыкание контура
                        if (current_x, current_y) == start_point and len(contour) > 3:
                            return contour
                        break

            if not found:
                break

        return contour

    def find_boundaries_with_holes(self, start_x, start_y):
        """
        Находит все границы (внешнюю и внутренние) связной области
        1. Обход внешней границы
        2. Сканирование внутренних строк для поиска отверстий
        """
        target_color = self.image.get_at((start_x, start_y))
        all_boundaries = []
        visited = set()

        print(f"\nЦвет области: {target_color}")

        # Шаг 1: Находим все точки области с помощью заливки
        area_points = self.flood_fill_area(start_x, start_y, target_color)
        print(f"Найдено точек в области: {len(area_points)}")

        if not area_points:
            return []

        # Шаг 2: Находим границы области
        # Для каждой точки области проверяем, является ли она граничной
        boundary_candidates = set()
        for x, y in area_points:
            # Проверяем соседей
            is_boundary_point = False
            for dx, dy in self.directions:
                nx, ny = x + dx, y + dy
                if self.is_boundary(nx, ny, target_color):
                    is_boundary_point = True
                    break
            if is_boundary_point:
                boundary_candidates.add((x, y))

        print(f"Найдено граничных точек: {len(boundary_candidates)}")

        # Шаг 3: Группируем граничные точки в контуры
        # Сортируем по Y, затем по X для построчного обхода
        sorted_candidates = sorted(boundary_candidates, key=lambda p: (p[1], p[0]))

        # Находим связные компоненты границ
        remaining = set(sorted_candidates)

        while remaining:
            start_point = min(remaining, key=lambda p: (p[1], p[0]))

            contour = self.trace_boundary_component(start_point, boundary_candidates)

            if contour:
                all_boundaries.append(contour)
                # Удаляем обработанные точки
                for point in contour:
                    remaining.discard(point)
                print(f"Найден контур с {len(contour)} точками")
            else:
                # Если не смогли обойти, просто удаляем точку
                remaining.discard(start_point)

        return all_boundaries

    def trace_boundary_component(self, start_point, boundary_set):
        """
        Обходит одну связную компоненту границы
        """
        contour = []
        visited = set()
        stack = [start_point]

        while stack:
            point = stack.pop()
            if point in visited:
                continue

            if point not in boundary_set:
                continue

            visited.add(point)
            contour.append(point)

            x, y = point
            # Добавляем соседей в стек
            for dx, dy in self.directions:
                nx, ny = x + dx, y + dy
                neighbor = (nx, ny)
                if neighbor in boundary_set and neighbor not in visited:
                    stack.append(neighbor)

        return contour

    def flood_fill_area(self, start_x, start_y, target_color):
        """
        Находит все точки связной области с помощью заливки
        """
        if self.is_boundary(start_x, start_y, target_color):
            return []

        area = []
        visited = set()
        stack = [(start_x, start_y)]

        while stack:
            x, y = stack.pop()

            if (x, y) in visited:
                continue

            if not (0 <= x < self.width and 0 <= y < self.height):
                continue

            if self.is_boundary(x, y, target_color):
                continue

            visited.add((x, y))
            area.append((x, y))

            for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in visited:
                    stack.append((nx, ny))

        return area

    def draw_boundary(self):
        """
        Рисует все границы поверх изображения
        """
        if self.boundary_points and self.show_boundary:
            colors = [
                (255, 0, 0),  
                (0, 255, 0),  
                (0, 0, 255),  
                (255, 255, 0),
                (255, 0, 255),
            ]

            for contour_idx, contour in enumerate(self.boundary_points):
                color = colors[contour_idx % len(colors)]

                if len(contour) > 1:
                    points = [(x + self.image_offset[0], y + self.image_offset[1]) 
                              for (x, y) in contour]

                    pg.draw.lines(self.screen, color, True, points, 2)

                else:
                    x, y = contour[0]
                    px = x + self.image_offset[0]
                    py = y + self.image_offset[1]
                    pg.draw.circle(self.screen, color, (px, py), 2)


    def run(self):
        """
        Запускает обход всех границ области
        """
        x0, y0 = self.have_clicked_at

        print(f"\nНачинаем поиск границ с точки ({x0}, {y0})")

        boundaries = self.find_boundaries_with_holes(x0, y0)

        if boundaries:
            self.boundary_points = boundaries
            self.show_boundary = True

            print(f"\nВсего найдено контуров: {len(boundaries)}")
            for i, contour in enumerate(boundaries):
                print(f"Контур {i+1}: {len(contour)} точек")
                if i == 0:
                    print(f"  (внешняя граница)")
                else:
                    print(f"  (отверстие {i})")
        else:
            print("Границы не найдены!")
            self.boundary_points = []
            self.show_boundary = False

    def update(self, event):
        self.images_loader.update(event)
        if self.images_loader.have_changed:
            self.image = self.images_loader.get_image()
            self.width, self.height = self.image.get_size()
            self.boundary_points = []
            self.show_boundary = False

        self.have_clicked = False
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            img_x = mx - self.image_offset[0]
            img_y = my - self.image_offset[1]
            if 0 <= img_x < self.width and 0 <= img_y < self.height:
                self.have_clicked = True
                self.have_clicked_at = (img_x, img_y)

        if event.type == pg.KEYDOWN and event.key == pg.K_r:
            self.boundary_points = []
            self.show_boundary = False
            print("\nГраница сброшена")

    def draw(self):
        self.images_loader.draw()
        self.screen.blit(self.image, self.image_offset)
        self.draw_boundary()


if __name__ == '__main__':
    pg.init()
    screen_size = (240*5, 136*5)
    screen = pg.display.set_mode(screen_size, pg.RESIZABLE)
    pg.display.set_caption("Выделение границы - R для сброса")
    clock = pg.time.Clock()

    tracer = BoundaryTracer(screen)

    print("=" * 60)
    print("Инструкция:")
    print("1. Кликните ВНУТРИ области (не на границе!)")
    print("2. Границы будут выделены разными цветами:")
    print("   - Красный: внешняя граница")
    print("   - Зеленый, синий и др.: отверстия")
    print("3. Нажмите R для сброса")
    print("4. < > - переключение изображений")
    print("=" * 60)

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.VIDEORESIZE:
                screen_size = (event.w, event.h)
            tracer.update(event)

        if tracer.have_clicked:
            tracer.run()

        screen.fill((30, 30, 30))
        tracer.draw()
        pg.display.flip()
        clock.tick(20)