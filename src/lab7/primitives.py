import numpy as np
import pygame
import config
from typing import List, Tuple, Optional


class Vector2:
    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y


class Color:
    def __init__(self, r: int = 0, g: int = 0, b: int = 0, a: int = 255):
        self.r = r
        self.g = g
        self.b = b
        self.a = a


class Rectangle:
    def __init__(self, x: float = 0.0, y: float = 0.0, width: float = 0.0, height: float = 0.0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height


class Point:
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z

    def to_homogeneous(self):
        return np.array([self.x, self.y, self.z, 1.0])

    def from_homogeneous(self, h):
        self.x = h[0]
        self.y = h[1]
        self.z = h[2]

    def __str__(self):
        return f"({self.x:.1f}, {self.y:.1f}, {self.z:.1f})"


class Polygon:
    def __init__(self, points: List[Point] = []):
        self.vertices = points.copy()

    def add_vertex(self, p: Point):
        self.vertices.append(p)

    def get_center(self) -> Point:
        if not self.vertices:
            return Point(0, 0, 0)
        cx = sum(v.x for v in self.vertices) / len(self.vertices)
        cy = sum(v.y for v in self.vertices) / len(self.vertices)
        cz = sum(v.z for v in self.vertices) / len(self.vertices)
        return Point(cx, cy, cz)

    def apply_transformation(self, matrix: np.ndarray):
        for vertex in self.vertices:
            h = vertex.to_homogeneous()
            transformed = np.dot(matrix, h)
            vertex.from_homogeneous(transformed)

    def __len__(self):
        return len(self.vertices)

    def __iter__(self):
        return iter(self.vertices)

    def __getitem__(self, index):
        return self.vertices[index]

class Object:
    def __init__(self, polies: List[Polygon] = []):
        self.polygons = polies.copy()

    def add_face(self, p: Polygon):
        self.polygons.append(p)

    def get_center(self) -> Point:
        all_vertices = []
        for poly in self.polygons:
            all_vertices.extend(poly.vertices)

        if not all_vertices:
            return Point(0, 0, 0)

        cx = sum(v.x for v in all_vertices) / len(all_vertices)
        cy = sum(v.y for v in all_vertices) / len(all_vertices)
        cz = sum(v.z for v in all_vertices) / len(all_vertices)
        return Point(cx, cy, cz)

    def apply_transformation(self, matrix: np.ndarray):
        for poly in self.polygons:
            poly.apply_transformation(matrix)

    def __len__(self):
        return len(self.polygons)

    def __iter__(self):
        return iter(self.polygons)

    def __getitem__(self, index):
        return self.polygons[index]


def create_cube() -> Object:
    points = [
        Point(0.0, 0.0, 0.0),
        Point(200.0, 0.0, 0.0),
        Point(200.0, 200.0, 0.0),
        Point(0.0, 200.0, 0.0),
        Point(0.0, 0.0, 200.0),
        Point(200.0, 0.0, 200.0),
        Point(200.0, 200.0, 200.0),
        Point(0.0, 200.0, 200.0)
    ]

    cube = Object([
        Polygon([points[0], points[1], points[2], points[3]]),
        Polygon([points[0], points[1], points[5], points[4]]),
        Polygon([points[1], points[2], points[6], points[5]]),
        Polygon([points[2], points[3], points[7], points[6]]),
        Polygon([points[0], points[3], points[7], points[4]]),
        Polygon([points[4], points[5], points[6], points[7]])
    ])
    return cube


def create_tetrahedron() -> Object:
    cube = create_cube()
    tetr = Object()

    vert = [
        cube.polygons[0].vertices[1],
        cube.polygons[0].vertices[3],
        cube.polygons[5].vertices[0],
        cube.polygons[5].vertices[2]
    ]

    tetr.add_face(Polygon([vert[1], vert[2], vert[3]]))
    tetr.add_face(Polygon([vert[0], vert[1], vert[2]]))
    tetr.add_face(Polygon([vert[0], vert[2], vert[3]]))
    tetr.add_face(Polygon([vert[0], vert[3], vert[1]]))

    return tetr


def create_octahedron() -> Object:
    cube = create_cube()
    vert = []
    for f in cube.polygons:
        vert.append(f.get_center())

    octa = Object()
    octa.add_face(Polygon([vert[0], vert[1], vert[4]]))
    octa.add_face(Polygon([vert[5], vert[1], vert[4]]))

    for i in range(3):
        octa.add_face(Polygon([vert[0], vert[i + 1], vert[(i + 1) % 4 + 1]]))
        octa.add_face(Polygon([vert[5], vert[i + 1], vert[(i + 1) % 4 + 1]]))

    return octa


def create_icosahedron() -> Object:
    phi = (1 + 5**0.5) / 2
    a = 100

    vertices = [
        Point(-a, phi * a, 0), Point(a, phi * a, 0), Point(-a, -phi * a, 0), Point(a, -phi * a, 0),
        Point(0, -a, phi * a), Point(0, a, phi * a), Point(0, -a, -phi * a), Point(0, a, -phi * a),
        Point(phi * a, 0, -a), Point(phi * a, 0, a), Point(-phi * a, 0, -a), Point(-phi * a, 0, a)
    ]

    icosa = Object()

    faces_indices = [
        [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
        [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
        [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
    ]

    for face in faces_indices:
        icosa.add_face(Polygon([vertices[face[0]], vertices[face[1]], vertices[face[2]]]))

    return icosa

def create_dodecahedron() -> Object:
    phi =  1 + np.sqrt(5) / 2;
    a = 100

    vert = [
        Point(a, a, a), Point(a,a,-a), Point(a,-a,a), Point(a,-a,-a),
        Point(-a, a, a), Point(-a,a,-a), Point(-a,-a,a), Point(-a,-a,-a),
        Point(0, 1 / phi * a, phi * a), Point(0, 1 / phi * a, -phi * a), Point(0, -1/phi * a, phi * a), Point(0, -1/phi * a, -phi * a),
        Point(1 / phi * a, phi * a, 0), Point(1 / phi * a, -phi * a, 0), Point(-1/phi * a, phi * a, 0), Point(-1/phi * a, -phi * a, 0),
        Point(phi * a, 0, 1 / phi * a), Point(phi * a, 0, -1 / phi * a), Point(-phi * a, 0, 1/phi * a), Point(-phi * a, 0, -1/phi * a),
    ]

    dodeca = Object()

    face_groups = [
        [0, 8, 10, 2, 16],
        [0, 16, 17, 1, 12],
        [0, 12, 14, 4, 8],
        [17, 3, 11, 9, 1],
        [2, 10, 6, 15, 13],
        [13, 15, 7, 11, 3],
        [17, 16, 2, 13, 3],
        [14, 5, 19, 18, 4],
        [9, 11, 7, 19, 5],
        [18, 19, 7, 15, 6],
        [12, 1, 9, 5, 14],
        [4, 18, 6, 10, 8]
    ]

    for group in face_groups:
        face_vertices = [vert[i] for i in group]
        dodeca.add_face(Polygon(face_vertices))

    return dodeca