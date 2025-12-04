import pygame
import math
import numpy as np
from typing import List, Tuple, Optional
import config
from transformations import *
from primitives import *
from UI import *
from camera import *
# from z_buffer_renderer import render_poly_zbuffer


WIDTH = 0
HEIGHT = 0

def get_view_matrix():
    """Генерирует полную матрицу трансформации камеры (View Matrix)"""
    # 1. Смещение мира, чтобы камера стала центром (0, 0, 0)
    t_matrix = translation_matrix(-camera.x, -camera.y, -camera.z)

    # 2. Поворот мира вокруг камеры (обратный поворот камеры)
    rot_y_matrix = rotation_y_matrix(-camera.angle_y)
    rot_x_matrix = rotation_x_matrix(-camera.angle_x)
    rot_z_matrix = rotation_z_matrix(-camera.angle_z)

    # Итоговая матрица: Сначала смещение, потом повороты
    view_matrix = np.dot(rot_z_matrix, np.dot(rot_x_matrix, np.dot(rot_y_matrix, t_matrix)))
    return view_matrix

class PolygonProjection:
    def __init__(self, points: List[List[float]] = [], depth: float = 0.0):
        self.vertices = points.copy()
        self.color = config.BLUE
        self.depth = depth  # Средняя глубина полигона для Z-буфера
        self.center_2d = None  # Для рисования нормали
        self.normal_end_2d = None  # Конец вектора нормали в 2D
        self.texture = None;

    def add_vertex(self, point: List[float]):
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

        int_vertices = [(int(v[0]), int(v[1])) for v in self.vertices]

        # Рисуем заливку граней
        if show_faces:
            # fill_color = (max(0, self.color[0]-100), max(0, self.color[1]-100), max(0, self.color[2]-100))
            ##todo: заменить на отрисовку z-bufferом
            render_poly_zbuffer(screen, self, self.texture)
            ##pygame.draw.polygon(screen, fill_color, int_vertices)

        # Рисуем каркас (рёбра)
        if show_wireframe:
            ##todo: заменить на отрисовку z-bufferом
            pygame.draw.polygon(screen, self.color, int_vertices, config.LINE_WIDTH)

    def draw_normal(self, screen, color: Tuple[int, int, int] = (255, 0, 0)):
        """Рисует вектор нормали полигона"""
        if self.center_2d and self.normal_end_2d:
            start_pos = (int(self.center_2d[0]), int(self.center_2d[1]))
            end_pos = (int(self.normal_end_2d[0]), int(self.normal_end_2d[1]))

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

                # print(self.center_2d)

                pygame.draw.line(screen, color, end_pos, (int(left_x), int(left_y)), 2)
                pygame.draw.line(screen, color, end_pos, (int(right_x), int(right_y)), 2)
    def __len__(self):
        return len(self.vertices)


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
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 1]
        ])
        depth = transformed_vertex_h[2] # Глубина для аксонометрии
    else:  # Перспективная
        c = config.V_POINT
        projection_matrix = np.array([
            [c, 0, 0, 0],
            [0, c, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 1, 0]
        ])
        depth = transformed_vertex_h[2] # Используем Z координату как глубину

    projected_vertex = np.dot(projection_matrix, transformed_vertex_h)

    # print(projected_vertex)

    if abs(projected_vertex[3]) > 1e-6:
        # print('lol')
        x_normalized = projected_vertex[0] / projected_vertex[3]
        y_normalized = projected_vertex[1] / projected_vertex[3]
        screen_x = x_normalized + window.center.x
        screen_y = y_normalized + window.center.y
        return [screen_x, screen_y, depth, vertex.u, vertex.v]

    return None


def render_polygon(poly: Polygon, method: str, window: WindowInfo):
    """Возвращает проецированный полигон с информацией о глубине и нормали"""
    pp = PolygonProjection()
    depths = []

    for v in poly.vertices:
        p = render_point(v, method, window)
        if p is None:
            return None
        pp.add_vertex((p[0], p[1], p[2], p[3], p[4]))
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
    projected_obj = []
    if not obj.polygons:
        return projected_obj

    obj_center = obj.get_center()

    # 1. Получаем матрицу вида один раз для всего объекта
    view_matrix = get_view_matrix()

    # Списки для сортировки
    polygons_to_render = []

    for p in obj.polygons:
        # Рассчитываем нормаль в системе координат объекта (как раньше)
        p.calculate_normal(obj_center)
        if p.normal is None:
            continue

        # А. Переводим ЦЕНТР полигона в пространство камеры (View Space)
        poly_center = p.get_center()
        center_vec = np.array([poly_center.x, poly_center.y, poly_center.z, 1])
        center_view = np.dot(view_matrix, center_vec)  # Координаты относительно камеры

        # Б. Переводим НОРМАЛЬ в пространство камеры
        # Важно: w=0, чтобы перемещение камеры не влияло на вектор направления, только поворот
        normal_vec = np.array([p.normal.x, p.normal.y, p.normal.z, 0])
        normal_view = np.dot(view_matrix, normal_vec)

        is_visible = False

        if method == "Аксонометрическая":
            # В ортогональной проекции мы смотрим строго вдоль оси Z.
            # Нам не важна позиция полигона (center_view), важен только поворот нормали.
            # В View Space камера смотрит вперед. Если Z-компонента нормали смотрит
            # "на нас" (противоположно оси взгляда), грань видима.
            # Попробуйте > 0. Если грани исчезнут - поменяйте на < 0.
            is_visible = normal_view[2] > 0

        else: # Перспективная
            # В перспективе мы смотрим из точки (0,0,0) в точку center_view.
            # Вектор взгляда = center_view (так как camera в 0,0,0).
            view_vector = center_view[0:3]

            # Скалярное произведение
            dot_product = np.dot(normal_view[0:3], view_vector)

            # Если скалярное произведение < 0, значит угол между нормалью и
            # лучом зрения тупой (они смотрят навстречу друг другу).
            # Поменяйте знак на > 0, если грани вывернуты наизнанку.
            is_visible = dot_product < 0

        if is_visible:
            rendered_poly = render_polygon(p, method, window)
            if rendered_poly:
                polygons_to_render.append(rendered_poly)

    if use_zbuffer:
        # polygons_to_render.sort(key=lambda x: x.depth, reverse=True)
        polygons_to_render.sort(key=lambda x: x.depth, reverse=False)
        projected_obj = polygons_to_render
    else:
        # Если Z-буфер выключен, сортируем просто по дальности (Painter's algo)
        # Но лучше всегда использовать Z-сортировку для корректности
        polygons_to_render.sort(key=lambda x: x.depth, reverse=False)
        projected_obj = polygons_to_render

    return projected_obj


def render_multiple_objects(objects: List[Object], method: str, window: WindowInfo, use_zbuffer: bool = True):
    all_polygons = []

    # Получаем матрицу один раз на кадр (оптимизация)
    view_matrix = get_view_matrix()

    for obj in objects:
        if not obj.polygons:
            continue

        obj_center = obj.get_center()

        for p in obj.polygons:
            p.calculate_normal(obj_center)
            if p.normal is None:
                continue

            # === ТА ЖЕ ЛОГИКА ===
            poly_center = p.get_center()

            # Трансформация центра
            center_vec = np.array([poly_center.x, poly_center.y, poly_center.z, 1])
            center_view = np.dot(view_matrix, center_vec)

            # Трансформация нормали (w=0!)
            normal_vec = np.array([p.normal.x, p.normal.y, p.normal.z, 0])
            normal_view = np.dot(view_matrix, normal_vec)

            # Проверка
            dot_product = np.dot(normal_view[0:3], -center_view[0:3])

            if dot_product > 0:
                rendered_poly = render_polygon(p, method, window)
                if rendered_poly:
                    all_polygons.append(rendered_poly)
            # ====================

    if use_zbuffer:
        #all_polygons.sort(key=lambda x: x.depth, reverse=True)
        all_polygons.sort(key=lambda x: x.depth, reverse=False)

    return all_polygons


    #============ Проблемы с зависимостями, Z-buffer будет здесь

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

# Вычислять каждый раз - медленно. Переношу в rasterize_triangle
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

# rasterize_triangle без необходимости в трёхмерном полигоне (у вершин уже есть depth)
def rasterize_triangle(screen, vertices_2d, color, color_border, texture = None):
    """Растеризует треугольник и обновляет Z-буфер."""
    v0 = vertices_2d.vertices[0]
    v1 = vertices_2d.vertices[1]
    v2 = vertices_2d.vertices[2]

    # Ограничивающий прямоугольник треугольника
    min_x = max(0, int(min(v0[0], v1[0], v2[0])))
    max_x = min(WIDTH - 1, int(max(v0[0], v1[0], v2[0])))
    min_y = max(0, int(min(v0[1], v1[1], v2[1])))
    max_y = min(HEIGHT - 1, int(max(v0[1], v1[1], v2[1])))


    vec_ab = (v1[0] - v0[0], v1[1] - v0[1])
    vec_ac = (v2[0] - v0[0], v2[1] - v0[1])
    d00 = vec_ab[0] * vec_ab[0] + vec_ab[1] * vec_ab[1]
    d01 = vec_ab[0] * vec_ac[0] + vec_ab[1] * vec_ac[1]
    d11 = vec_ac[0] * vec_ac[0] + vec_ac[1] * vec_ac[1]
    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            vec_ap = (x - v0[0], y - v0[1])
            d20 = vec_ap[0] * vec_ab[0] + vec_ap[1] * vec_ab[1]
            d21 = vec_ap[0] * vec_ac[0] + vec_ap[1] * vec_ac[1]

            denom = d00 * d11 - d01 * d01
            if abs(denom) < 1e-5:
                v, w, u = -1, -1, -1

            v = (d11 * d20 - d01 * d21) / denom
            w = (d00 * d21 - d01 * d20) / denom
            u = 1.0 - v - w
            # u, v, w = barycentric_coords((x, y), v0, v1, v2)

            if u >= 0 and v >= 0 and w >= 0:
                # Интерполяция Z-координаты
                z = u * v0[2] + v * v1[2] + w * v2[2]

                if z < z_buffer[x, y]:
                    z_buffer[x, y] = z
                    if u < 2e-2 or v< 2e-2 or w< 2e-2:
                        screen.set_at((x, y), color_border)
                    else: 
                        if texture == None:
                            screen.set_at((x, y), color)
                        else:
                            t_x = 1 - (u * v0[3] + v * v1[3] + w * v2[3])
                            t_y = 1 - (u * v0[4] + v * v1[4] + w * v2[4])
                            t_x *= texture.get_width()
                            t_y *= texture.get_height()
                            if t_x >= texture.get_width():
                                t_x -= 1;
                            if t_y >= texture.get_height():
                                t_y -= 1;
                            if t_x < 0:
                                t_x = np.float64(0);
                            if t_y < 0:
                                t_y = np.float64(0);
                            t_color = texture.get_at((t_x.astype(int), t_y.astype(int)))
                            screen.set_at((x, y), t_color)

def render_poly_zbuffer(screen, poly, texture = None):
    polys = []
    if len(poly) > 3:
        for i in range(len(poly) - 2):
            pp = PolygonProjection([poly.vertices[0], poly.vertices[i + 1], poly.vertices[i + 2]])
            pp.depth = (poly.vertices[0][2] + poly.vertices[i + 1][2] + poly.vertices[i + 2][2]) / 3;
            polys.append(pp)
    else:
        polys = [poly] 

    for p in polys:
        rasterize_triangle(screen, p, (0, 0, 255), (0, 0, 0), texture)