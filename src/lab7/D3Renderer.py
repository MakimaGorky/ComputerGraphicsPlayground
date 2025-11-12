import pygame
import math
from typing import List, Tuple, Optional
import config
from transformations import *
from primitives import *
from UI import *


PIVOT = (800, 800)  # hold my 🍺
Z_PIVOT = -1000  # hold my 🍺
WIDTH = 0
HEIGHT = 0



class PolygonProjection:
    def __init__(self, points: List[Tuple[float, float]] = []):
        self.vertices = points.copy()
        self.color = config.BLUE

    def add_vertex(self, point: Tuple[float, float]):
        self.vertices.append(point)

    def draw(self, screen):
        def draw(self, screen):
            # Пропускаем отрисовку, если у полигона вообще нет вершин после проекции и отсечения.
            if not self.vertices:
                return

            try:
                # Преобразуем все вершины в целочисленные координаты для Pygame.
                # Именно здесь может произойти сбой, если v содержит 'inf' или 'nan'.
                int_vertices = [(int(v[0] + PIVOT[0]), int(v[1] + PIVOT[1])) for v in self.vertices]

                # Теперь рисуем в зависимости от количества получившихся вершин.
                # Если после отсечения от полигона осталась только одна или две точки.
                if len(int_vertices) == 1:
                    pygame.draw.circle(screen, self.color, int_vertices[0], config.POINT_RADIUS)

                elif len(int_vertices) == 2:
                    pygame.draw.line(screen, self.color, int_vertices[0], int_vertices[1], config.LINE_WIDTH)

                elif len(int_vertices) >= 3:
                    pygame.draw.polygon(screen, self.color, int_vertices, config.LINE_WIDTH)
                    # Рисуем красные точки поверх вершин полигона для наглядности
                    for v in int_vertices:
                        pygame.draw.circle(screen, config.RED, v, config.VERTEX_RADIUS)

            except (TypeError, ValueError, OverflowError) as e:
                # ЭТОТ БЛОК -- НАШ ЗАЩИТНЫЙ МЕХАНИЗМ И ДИАГНОСТИКА
                # Если преобразование в int() или сама отрисовка не удались, мы поймаем ошибку.
                # Это предотвратит падение всей программы.

                # Раскомментируйте следующие строки, если хотите видеть в консоли,
                # какие именно "сломанные" полигоны пропускаются.
                print("="*50)
                print(f"ОШИБКА ОТРИСОВКИ: Пропущен некорректный полигон.")
                print(f"Сообщение об ошибке: {e}")
                print(f"Проблемные данные (self.vertices): {self.vertices}")
                print("="*50)

                # Мы не прерываем программу, а просто пропускаем отрисовку этого одного полигона.
                return


def render_point(vertex: Point, transform_matrix: np.ndarray, method: str, window: WindowInfo):
    # Сначала применяем трансформацию объекта в мире (поворот, перенос, масштаб)
    # Исходная точка vertex НЕ МЕНЯЕТСЯ
    world_vertex = np.dot(transform_matrix, vertex.to_homogeneous())

    # Смещаем по Z для камеры
    world_vertex[2] += Z_PIVOT

    if method == "Аксонометрическая":
        a = np.radians(config.ANGLE)
        projection_matrix = np.array([
            [1, 0, 0.5 * np.cos(a), 0],
            [0, 1, 0.5 * np.cos(a), 0],
            [0, 0, 0, 0],
            [0, 0, 0, 1]
        ])
    else:  # Перспективная
        c = config.V_POINT
        projection_matrix = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 0],
            [0, 0, -1 / c, 1]
        ])

    # Применяем проекцию, чтобы получить 2D-координаты
    projected_vertex = np.dot(projection_matrix, world_vertex)
    w = projected_vertex[3]

    if abs(w) < 1e-6:
        return None

    x_normalized = projected_vertex[0] / w
    y_normalized = projected_vertex[1] / w
    return (x_normalized, y_normalized)


def render_polygon(poly: Polygon, transform_matrix: np.ndarray, method: str, window: WindowInfo):
    valid_points = []
    for v in poly.vertices:
        p = render_point(v, transform_matrix, method, window)
        if p is not None:
            valid_points.append(p)
    return PolygonProjection(valid_points)


def render_object(scene_obj: SceneObject, method: str, window: WindowInfo):
    projected_obj = []
    # Передаем не только модель, но и ее матрицу трансформации
    for p in scene_obj.model.polygons:
        projected_obj.append(render_polygon(p, scene_obj.transform, method, window))
    return projected_obj

