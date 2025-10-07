"""Геометрические функции"""
import math
from typing import Tuple, Optional


def line_intersection(p1: Tuple[float, float], p2: Tuple[float, float],
                      p3: Tuple[float, float], p4: Tuple[float, float]) -> Optional[Tuple[float, float]]:
    """
    Найти точку пересечения двух отрезков
    Использует параметрическое представление прямых
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

    if abs(denom) < 1e-10:
        return None  # Параллельные или совпадающие линии

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

    # Проверяем, что пересечение находится на обоих отрезках
    if 0 <= t <= 1 and 0 <= u <= 1:
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)
        return (x, y)

    return None


def point_position_relative_to_edge(point: Tuple[float, float],
                                    edge_start: Tuple[float, float],
                                    edge_end: Tuple[float, float]) -> str:
    """
    Классификация положения точки относительно ориентированного ребра
    Использует знак векторного произведения
    """
    px, py = point
    x1, y1 = edge_start
    x2, y2 = edge_end

    # Векторное произведение (cross product)
    cross = (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)

    if abs(cross) < 1e-6:
        return "на прямой"
    elif cross > 0:
        return "справа"
    else:
        return "слева"


def point_in_polygon(point: Tuple[float, float], vertices: list) -> bool:
    """
    Проверка принадлежности точки полигону
    Алгоритм: метод лучей (ray casting)
    """
    if len(vertices) < 3:
        return False

    x, y = point
    n = len(vertices)
    inside = False

    j = n - 1
    for i in range(n):
        xi, yi = vertices[i]
        xj, yj = vertices[j]

        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside

        j = i

    return inside


def point_to_segment_distance(point: Tuple[float, float],
                              seg_start: Tuple[float, float],
                              seg_end: Tuple[float, float]) -> float:
    """
    Вычислить расстояние от точки до отрезка
    """
    px, py = point
    x1, y1 = seg_start
    x2, y2 = seg_end

    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)

    # Проекция точки на прямую
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))

    nearest_x = x1 + t * dx
    nearest_y = y1 + t * dy

    return math.sqrt((px - nearest_x) ** 2 + (py - nearest_y) ** 2)