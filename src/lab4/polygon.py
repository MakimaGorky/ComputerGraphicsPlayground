"""Класс полигона"""
import pygame
import numpy as np
from typing import List, Tuple
import config


class Polygon:
    """
    Класс для представления полигона
    Поддерживает точки (1 вершина), ребра (2 вершины) и многоугольники (3+ вершин)
    """

    def __init__(self):
        self.vertices: List[Tuple[float, float]] = []
        self.color = config.BLUE

    def add_vertex(self, x: float, y: float):
        """Добавить вершину в полигон"""
        self.vertices.append((x, y))

    def get_center(self) -> Tuple[float, float]:
        """Вычислить геометрический центр (центроид) полигона"""
        if not self.vertices:
            return (0, 0)

        cx = sum(v[0] for v in self.vertices) / len(self.vertices)
        cy = sum(v[1] for v in self.vertices) / len(self.vertices)
        return (cx, cy)

    def apply_transformation(self, matrix: np.ndarray):
        """
        Применить аффинное преобразование к полигону
        matrix: матрица 3x3 в однородных координатах
        """
        new_vertices = []
        for x, y in self.vertices:
            # Создаем вектор в однородных координатах [x, y, 1]
            point = np.array([x, y, 1])
            # Применяем матрицу преобразования
            new_point = matrix @ point
            new_vertices.append((new_point[0], new_point[1]))
        self.vertices = new_vertices

    def draw(self, screen):
        """Отрисовка полигона на экране"""
        if len(self.vertices) == 1:
            # Точка
            pygame.draw.circle(screen, self.color,
                               (int(self.vertices[0][0]), int(self.vertices[0][1])),
                               config.POINT_RADIUS)
        elif len(self.vertices) == 2:
            # Ребро
            pygame.draw.line(screen, self.color,
                             (int(self.vertices[0][0]), int(self.vertices[0][1])),
                             (int(self.vertices[1][0]), int(self.vertices[1][1])),
                             config.LINE_WIDTH)
        else:
            # Полигон
            int_vertices = [(int(v[0]), int(v[1])) for v in self.vertices]
            pygame.draw.polygon(screen, self.color, int_vertices, config.LINE_WIDTH)
            # Рисуем вершины
            for v in int_vertices:
                pygame.draw.circle(screen, config.RED, v, config.VERTEX_RADIUS)

    def __len__(self):
        return len(self.vertices)

    def __iter__(self):
        return iter(self.vertices)

    def __getitem__(self, index):
        return self.vertices[index]
