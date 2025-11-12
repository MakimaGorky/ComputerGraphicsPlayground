import pygame
import math
from typing import List, Tuple, Optional
import config
from transformations import *
from primitives import *
from UI import *
from camera import *


# PIVOT = (800, 800)  # hold my 🍺
# Z_PIVOT = -1000  # hold my 🍺
WIDTH = 0
HEIGHT = 0



class PolygonProjection:
    def __init__(self, points: List[Tuple[float, float]] = []):
        self.vertices = points.copy()
        self.color = config.BLUE

    def add_vertex(self, point: Tuple[float, float]):
        self.vertices.append(point)

    def draw(self, screen):
        if len(self.vertices) == 1:
            pygame.draw.circle(screen, self.color,
                               (int(self.vertices[0][0] + camera.x), int(self.vertices[0][1] + camera.y)),
                               config.POINT_RADIUS)
        elif len(self.vertices) == 2:
            pygame.draw.line(screen, self.color,
                             (int(self.vertices[0][0] + camera.x), int(self.vertices[0][1] + camera.y)),
                             (int(self.vertices[1][0] + camera.x), int(self.vertices[1][1] + camera.y)),
                             config.LINE_WIDTH)
        else:
            int_vertices = [(int(v[0] + camera.x), int(v[1] + camera.y)) for v in self.vertices]
            pygame.draw.polygon(screen, self.color, int_vertices, config.LINE_WIDTH)
            for v in int_vertices:
                pygame.draw.circle(screen, config.RED, v, config.VERTEX_RADIUS)


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

    if projected_vertex[3] != 0:
        x_normalized = projected_vertex[0] / projected_vertex[3]
        y_normalized = projected_vertex[1] / projected_vertex[3]
        return (x_normalized, y_normalized)

    return (0, 0)


def render_polygon(poly: Polygon, method: str, window: WindowInfo):
    pp = PolygonProjection()
    for v in poly.vertices:
        p = render_point(v, method, window)
        pp.add_vertex(p)
    return pp


def render_object(obj: Object, method: str, window: WindowInfo):
    projected_obj = []
    for p in obj.polygons:
        projected_obj.append(render_polygon(p, method, window))
    return projected_obj

