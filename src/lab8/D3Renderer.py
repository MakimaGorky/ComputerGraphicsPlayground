import pygame
import math
import numpy as np
from typing import List, Tuple, Optional
import config
from transformations import *
from primitives import *
from UI import *
from camera import *


WIDTH = 0
HEIGHT = 0


class PolygonProjection:
    def __init__(self, points: List[Tuple[float, float]] = [], depth: float = 0.0):
        self.vertices = points.copy()
        self.color = config.BLUE
        self.depth = depth  # Средняя глубина полигона для Z-буфера
        self.center_2d = None  # Для рисования нормали
        self.normal_end_2d = None  # Конец вектора нормали в 2D

    def add_vertex(self, point: Tuple[float, float]):
        self.vertices.append(point)

    def draw(self, screen, show_faces: bool = True, show_wireframe: bool = True):
        """
        Рисует полигон с возможностью отключения граней и каркаса

        Args:
            screen: Поверхность для рисования
            show_faces: Отображать ли заливку граней
            show_wireframe: Отображать ли каркас (рёбра)
        """
        if len(self.vertices) < 3:
            return

        int_vertices = [(int(v[0] + camera.x), int(v[1] + camera.y)) for v in self.vertices]

        # Рисуем заливку граней
        if show_faces:
            fill_color = (max(0, self.color[0]-100), max(0, self.color[1]-100), max(0, self.color[2]-100))
            pygame.draw.polygon(screen, fill_color, int_vertices)

        # Рисуем каркас (рёбра)
        if show_wireframe:
            pygame.draw.polygon(screen, self.color, int_vertices, config.LINE_WIDTH)

    def draw_normal(self, screen, color: Tuple[int, int, int] = (255, 0, 0)):
        """Рисует вектор нормали полигона"""
        if self.center_2d and self.normal_end_2d:
            start_pos = (int(self.center_2d[0] + camera.x), int(self.center_2d[1] + camera.y))
            end_pos = (int(self.normal_end_2d[0] + camera.x), int(self.normal_end_2d[1] + camera.y))

            # Рисуем линию нормали
            pygame.draw.line(screen, color, start_pos, end_pos, 2)

            # Рисуем стрелку на конце
            # Вычисляем направление
            dx = end_pos[0] - start_pos[0]
            dy = end_pos[1] - start_pos[1]
            length = np.sqrt(dx*dx + dy*dy)

            if length > 5:  # Рисуем стрелку только если вектор достаточно длинный
                # Нормализуем
                dx /= length
                dy /= length

                # Точки стрелки
                arrow_size = 8
                angle = np.pi / 6  # 30 градусов

                # Левая часть стрелки
                left_x = end_pos[0] - arrow_size * (dx * np.cos(angle) + dy * np.sin(angle))
                left_y = end_pos[1] - arrow_size * (dy * np.cos(angle) - dx * np.sin(angle))

                # Правая часть стрелки
                right_x = end_pos[0] - arrow_size * (dx * np.cos(angle) - dy * np.sin(angle))
                right_y = end_pos[1] - arrow_size * (dy * np.cos(angle) + dx * np.sin(angle))

                print(self.center_2d)

                pygame.draw.line(screen, color, end_pos, (int(left_x), int(left_y)), 2)
                pygame.draw.line(screen, color, end_pos, (int(right_x), int(right_y)), 2)


def render_point(vertex: Point, method: str, window: WindowInfo):
    """Возвращает 2D координаты и глубину точки после проекции"""
    vertex_h = np.array([vertex.x, vertex.y, vertex.z, 1])

    t_matrix = translation_matrix(-camera.x, -camera.y, -camera.z)

    rot_y_matrix = rotation_y_matrix(-camera.angle_y)
    rot_x_matrix = rotation_x_matrix(-camera.angle_x)
    rot_z_matrix = rotation_z_matrix(-camera.angle_z)

    view_matrix = np.dot(rot_z_matrix, np.dot(rot_x_matrix, np.dot(rot_y_matrix, t_matrix))) # <--- ВКЛЮЧАЕМ Z-ПОВОРОТ

    transformed_vertex_h = np.dot(view_matrix, vertex_h)

    if method == "Аксонометрическая":
        a = np.radians(config.ANGLE)
        projection_matrix = np.array([
            [1, 0, 0.5 * np.cos(a), 0],
            [0, 1, 0.5 * np.cos(a), 0],
            [0, 0, 0, 0],
            [0, 0, 0, 1]
        ])
        depth = vertex.z # + camera.z  # Глубина для аксонометрии
    else:  # Перспективная
        c = config.V_POINT
        projection_matrix = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 0],
            [0, 0, -1 / c,  1]
        ])
        depth = vertex.z # + camera.z  # Используем Z координату как глубину

    projected_vertex = np.dot(projection_matrix, transformed_vertex_h)

    # print(projected_vertex)

    if abs(projected_vertex[3]) > 1e-6:
        # print('lol')
        x_normalized = projected_vertex[0] / projected_vertex[3]
        y_normalized = projected_vertex[1] / projected_vertex[3]
        return (x_normalized, y_normalized, depth)

    return None


def render_polygon(poly: Polygon, method: str, window: WindowInfo):
    """Возвращает проецированный полигон с информацией о глубине и нормали"""
    pp = PolygonProjection()
    depths = []

    for v in poly.vertices:
        p = render_point(v, method, window)
        if p is None:
            return None
        pp.add_vertex((p[0], p[1]))
        depths.append(p[2])

    # Вычисляем среднюю глубину полигона для Z-буфера
    pp.depth = sum(depths) / len(depths)

    # Проецируем центр и конец вектора нормали для отрисовки
    if poly.normal:
        poly_center = poly.get_center()
        center_proj = render_point(poly_center, method, window)

        # Масштаб нормали для визуализации (можно настроить в config.py)
        normal_scale = getattr(config, 'NORMAL_SCALE', 50)
        normal_end = Point(
            poly_center.x + poly.normal.x * normal_scale,
            poly_center.y + poly.normal.y * normal_scale,
            poly_center.z + poly.normal.z * normal_scale
        )
        normal_end_proj = render_point(normal_end, method, window)

        if center_proj and normal_end_proj:
            pp.center_2d = (center_proj[0], center_proj[1])
            pp.normal_end_2d = (normal_end_proj[0], normal_end_proj[1])

    return pp


def render_object(obj: Object, method: str, window: WindowInfo, use_zbuffer: bool = True):
    """
    Рендерит объект с возможностью использования Z-буфера

    Args:
        obj: Объект для рендеринга
        method: Метод проекции ("Аксонометрическая" или "Перспективная")
        window: Информация об окне
        use_zbuffer: Использовать ли Z-буфер для сортировки

    Returns:
        Список проецированных полигонов
    """
    projected_obj = []

    if not obj.polygons:
        return projected_obj

    obj_center = obj.get_center()

    if use_zbuffer:
        # Используем Z-буфер: сортируем по средней глубине
        polygons_with_depth = []

        for p in obj.polygons:
            p.calculate_normal(obj_center)
            if p.normal is None:
                continue

            # Вычисляем вектор взгляда для отсечения задних граней
            poly_center = p.get_center()

            if method == "Перспективная":
                cam_poly_center_z = poly_center.z + camera.z
                view_vector = Point(-poly_center.x, -poly_center.y, config.V_POINT - cam_poly_center_z)
            else:
                view_vector = Point(0, 0, poly_center.z - camera.z)

            dot_product = (p.normal.x * view_vector.x +
                          p.normal.y * view_vector.y +
                          p.normal.z * view_vector.z)

            # Отсечение задних граней
            if dot_product > 0:
                rendered_poly = render_polygon(p, method, window)
                if rendered_poly:
                    polygons_with_depth.append(rendered_poly)

        # Сортируем полигоны по глубине (от дальних к ближним)
        # Чем больше depth (дальше от камеры), тем раньше рисуем
        polygons_with_depth.sort(key=lambda x: x.depth, reverse=True)
        projected_obj = polygons_with_depth

    else:
        # Старый метод без Z-буфера (только для выпуклых объектов)
        def get_avg_z(p):
            return sum(v.z for v in p.vertices) / len(p.vertices)

        sorted_polygons = sorted(obj.polygons, key=get_avg_z, reverse=False)

        for p in sorted_polygons:
            p.calculate_normal(obj_center)
            if p.normal is None:
                continue

            poly_center = p.get_center()

            if method == "Перспективная":
                cam_poly_center_z = poly_center.z + camera.z
                view_vector = Point(-poly_center.x, -poly_center.y, config.V_POINT - cam_poly_center_z)
            else:
                view_vector = Point(-poly_center.x, -poly_center.y, 1)

            dot_product = (p.normal.x * view_vector.x +
                          p.normal.y * view_vector.y +
                          p.normal.z * view_vector.z)

            if dot_product > 0:
                rendered_poly = render_polygon(p, method, window)
                if rendered_poly:
                    projected_obj.append(rendered_poly)

    return projected_obj


def render_multiple_objects(objects: List[Object], method: str, window: WindowInfo, use_zbuffer: bool = True):
    """
    Рендерит несколько объектов с корректной обработкой перекрытий через Z-буфер

    Args:
        objects: Список объектов для рендеринга
        method: Метод проекции
        window: Информация об окне
        use_zbuffer: Использовать ли Z-буфер
    """
    all_polygons = []

    for obj in objects:
        if not obj.polygons:
            continue

        obj_center = obj.get_center()

        for p in obj.polygons:
            p.calculate_normal(obj_center)
            if p.normal is None:
                continue

            poly_center = p.get_center()

            if method == "Перспективная":
                cam_poly_center_z = poly_center.z + camera.z
                view_vector = Point(-poly_center.x, -poly_center.y, config.V_POINT - cam_poly_center_z)
            else:
                view_vector = Point(0, 0, 1)

            dot_product = (p.normal.x * view_vector.x +
                          p.normal.y * view_vector.y +
                          p.normal.z * view_vector.z)

            if dot_product > 0:
                rendered_poly = render_polygon(p, method, window)
                if rendered_poly:
                    all_polygons.append(rendered_poly)

    if use_zbuffer:
        # Сортируем все полигоны всех объектов по глубине
        all_polygons.sort(key=lambda x: x.depth, reverse=True)

    return all_polygons