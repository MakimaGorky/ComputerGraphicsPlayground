import pygame
import math
from typing import List, Tuple, Optional
import config
from transformations import *
from primitives import *
from UI import *
from camera import *


WIDTH = 0
HEIGHT = 0


class PolygonProjection:
    def __init__(self, points: List[Tuple[float, float]] = []):
        self.vertices = points.copy()
        self.color = config.BLUE

    def add_vertex(self, point: Tuple[float, float]):
        self.vertices.append(point)

    def draw(self, screen):
        if len(self.vertices) < 3:
            return

        fill_color = (max(0, self.color[0]-100), max(0, self.color[1]-100), max(0, self.color[2]-100))
        int_vertices = [(int(v[0] + camera.x), int(v[1] + camera.y)) for v in self.vertices]

        pygame.draw.polygon(screen, fill_color, int_vertices)
        pygame.draw.polygon(screen, self.color, int_vertices, config.LINE_WIDTH)


def render_point(vertex: Point, method: str, window: WindowInfo):
    vertex_h = np.array([vertex.x, vertex.y, vertex.z + camera.z, 1])

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
            [0, 0, -1 / c,  1]
        ])

    projected_vertex = np.dot(projection_matrix, vertex_h)

    if projected_vertex[3] > 1e-6:
        x_normalized = projected_vertex[0] / projected_vertex[3]
        y_normalized = projected_vertex[1] / projected_vertex[3]
        return (x_normalized, y_normalized)

    return None


def render_polygon(poly: Polygon, method: str, window: WindowInfo):
    pp = PolygonProjection()
    for v in poly.vertices:
        p = render_point(v, method, window)
        if p is None:
             return None
        pp.add_vertex(p)
    return pp


def render_object(obj: Object, method:str, window: WindowInfo):
    projected_obj = []

    if not obj.polygons:
        return projected_obj

    obj_center = obj.get_center()

    def get_avg_z(p):
        return sum(v.z for v in p.vertices) / len(p.vertices)

    sorted_polygons = sorted(obj.polygons, key=get_avg_z, reverse=False)

    for p in sorted_polygons:
        p.calculate_normal(obj_center)
        if p.normal is None:
            continue

        view_vector: Point
        poly_center = p.get_center()

        if method == "Перспективная":
            cam_poly_center_z = poly_center.z + camera.z
            view_vector = Point(-poly_center.x, -poly_center.y, config.V_POINT - cam_poly_center_z)
        else:
            view_vector = Point(0, 0, 1)

        # print(p.normal)

        dot_product = (p.normal.x * view_vector.x +
                       p.normal.y * view_vector.y +
                       p.normal.z * view_vector.z)

        if dot_product > 0:
            rendered_poly = render_polygon(p, method, window)
            if rendered_poly:
                projected_obj.append(rendered_poly)

    return projected_obj