# z_buffer_renderer.py

import numpy as np
import pygame
from primitives import Polygon, Object, Point
from typing import List
import config

# Глобальный Z-буфер
z_buffer = None
WIDTH, HEIGHT = 0, 0

def init_z_buffer(width, height):
    """Инициализирует Z-буфер."""
    global z_buffer, WIDTH, HEIGHT
    WIDTH, HEIGHT = width, height
    z_buffer = np.full((width, height), np.inf, dtype=float)

def clear_z_buffer():
    """Очищает Z-буфер перед каждым кадром."""
    if z_buffer is not None:
        z_buffer.fill(np.inf)

def barycentric_coords(p, a, b, c):
    """Вычисляет барицентрические координаты точки p относительно треугольника a, b, c."""
    vec_ab = (b[0] - a[0], b[1] - a[1])
    vec_ac = (c[0] - a[0], c[1] - a[1])
    vec_ap = (p[0] - a[0], p[1] - a[1])

    d00 = vec_ab[0] * vec_ab[0] + vec_ab[1] * vec_ab[1]
    d01 = vec_ab[0] * vec_ac[0] + vec_ab[1] * vec_ac[1]
    d11 = vec_ac[0] * vec_ac[0] + vec_ac[1] * vec_ac[1]
    d20 = vec_ap[0] * vec_ab[0] + vec_ap[1] * vec_ab[1]
    d21 = vec_ap[0] * vec_ac[0] + vec_ap[1] * vec_ac[1]

    denom = d00 * d11 - d01 * d01
    if abs(denom) < 1e-5:
        return -1, -1, -1

    v = (d11 * d20 - d01 * d21) / denom
    w = (d00 * d21 - d01 * d20) / denom
    u = 1.0 - v - w
    return u, v, w

def rasterize_triangle(screen, vertices_2d, vertices_3d, color):
    """Растеризует треугольник и обновляет Z-буфер."""
    v0, v1, v2 = vertices_2d
    p0, p1, p2 = vertices_3d

    # Ограничивающий прямоугольник треугольника
    min_x = max(0, int(min(v0[0], v1[0], v2[0])))
    max_x = min(WIDTH - 1, int(max(v0[0], v1[0], v2[0])))
    min_y = max(0, int(min(v0[1], v1[1], v2[1])))
    max_y = min(HEIGHT - 1, int(max(v0[1], v1[1], v2[1])))

    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            u, v, w = barycentric_coords((x, y), v0, v1, v2)

            if u >= 0 and v >= 0 and w >= 0:
                # Интерполяция Z-координаты
                z = u * p0.z + v * p1.z + w * p2.z

                if z < z_buffer[x, y]:
                    z_buffer[x, y] = z
                    screen.set_at((x, y), color)


def render_object_zbuffer(screen, obj: Object, view_matrix, projection_matrix):
    """Рендерит объект с использованием Z-буфера."""

    # 1. Применяем трансформации и получаем вершины в пространстве камеры
    transformed_vertices = {}
    for poly in obj.polygons:
        for vertex in poly.vertices:
            if id(vertex) not in transformed_vertices:
                # Применяем матрицу вида, но пока не проекцию
                h_vertex = np.dot(view_matrix, vertex.to_homogeneous())
                transformed_vertices[id(vertex)] = Point(h_vertex[0], h_vertex[1], h_vertex[2])

    # 2. Проецируем вершины и рендерим полигоны
    for i, poly in enumerate(obj.polygons):
        # Разбиваем полигон на треугольники (если он не треугольный)
        if len(poly.vertices) < 3:
            continue

        color = config.COLORS[i % len(config.COLORS)] # Дадим каждой грани свой цвет

        # Создаем веер треугольников из первой вершины
        for j in range(1, len(poly.vertices) - 1):
            p0 = transformed_vertices[id(poly.vertices[0])]
            p1 = transformed_vertices[id(poly.vertices[j])]
            p2 = transformed_vertices[id(poly.vertices[j+1])]

            # Проецируем вершины треугольника
            projected_triangle = []
            for p in [p0, p1, p2]:
                h_vertex = np.array([p.x, p.y, p.z, 1])
                proj_v = np.dot(projection_matrix, h_vertex)
                if proj_v[3] != 0:
                    px = (proj_v[0] / proj_v[3] + 1) * WIDTH / 2
                    py = (-proj_v[1] / proj_v[3] + 1) * HEIGHT / 2
                    projected_triangle.append((px, py))
                else:
                    projected_triangle.append((0,0)) # В случае ошибки

            if len(projected_triangle) == 3:
                 rasterize_triangle(screen, projected_triangle, [p0, p1, p2], color)