
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
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0, u: float = 0.0, v: float = 0.0):
        self.x = x
        self.y = y
        self.z = z
        self.u = u
        self.v = v

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
        self.normal: Optional[Point] = None # <-- НОВЫЙ АТРИБУТ

    def add_vertex(self, p: Point):
        self.vertices.append(p)

    def get_center(self) -> Point:
        if not self.vertices:
            return Point(0, 0, 0)
        cx = sum(v.x for v in self.vertices) / len(self.vertices)
        cy = sum(v.y for v in self.vertices) / len(self.vertices)
        cz = sum(v.z for v in self.vertices) / len(self.vertices)
        return Point(cx, cy, cz)

    # ===== НОВЫЙ МЕТОД =====
    def calculate_normal(self, object_center: Point):
        """Вычисляет вектор нормали, направленный 'наружу' от центра объекта."""
        if len(self.vertices) < 3:
            self.normal = None
            return

        # Берем первые три вершины для определения плоскости
        v0 = self.vertices[0]
        v1 = self.vertices[1]
        v2 = self.vertices[2]

        # Создаем два вектора в плоскости полигона
        vec_a = Point(v1.x - v0.x, v1.y - v0.y, v1.z - v0.z)
        vec_b = Point(v2.x - v0.x, v2.y - v0.y, v2.z - v0.z)

        # Векторное произведение для получения нормали
        nx = vec_a.y * vec_b.z - vec_a.z * vec_b.y
        ny = vec_a.z * vec_b.x - vec_a.x * vec_b.z
        nz = vec_a.x * vec_b.y - vec_a.y * vec_b.x

        # Нормализация вектора
        length = np.sqrt(nx*nx + ny*ny + nz*nz)
        if length > 1e-9:
            nx /= length
            ny /= length
            nz /= length

        # Проверка направления нормали
        # Вектор от центра объекта к центру полигона
        center_to_face = Point(self.get_center().x - object_center.x,
                               self.get_center().y - object_center.y,
                               self.get_center().z - object_center.z)

        # Если скалярное произведение < 0, нормаль смотрит внутрь. Инвертируем ее.
        # dot_product = nx * center_to_face.x + ny * center_to_face.y + nz * center_to_face.z
        # if dot_product < 0:
        nx, ny, nz = -nx, -ny, -nz  

        self.normal = Point(nx, ny, nz)
    # =========================

    def apply_transformation(self, matrix: np.ndarray):
        for vertex in self.vertices:
            h = vertex.to_homogeneous()
            transformed = np.dot(matrix, h)
            vertex.from_homogeneous(transformed)

    def calculate_texture_coordinats(self):
        """
        Версия с автоматическим выбором осей для минимизации искажений
        """
        # Конвертируем всё в массивы numpy
        points = np.array([[p.x, p.y, p.z] for p in self.vertices])
        
        # Нормализуем нормаль
        normal = np.array([self.normal.x, self.normal.y, self.normal.z])
        n = normal / np.linalg.norm(normal)
        
        # Центрируем точки
        center = np.mean(points, axis=0)
        centered = points - center
        
        # Проецируем на плоскость
        dots = np.dot(centered, n)
        projected = centered - dots.reshape(-1, 1) * n
        
        # Находим главные оси через SVD (минимизация искажений)
        _, _, Vt = np.linalg.svd(projected)
        
        # Базисные векторы плоскости
        u_axis, v_axis = Vt[0], Vt[1]
        
        # Проецируем
        uv_array = projected @ np.column_stack([u_axis, v_axis])
        
        # Нормализуем к [0, 1]
        min_uv = np.min(uv_array, axis=0)
        max_uv = np.max(uv_array, axis=0)
        
        result = []
        for i in range(len(points)):
            u_val, v_val = uv_array[i]
            
            u_norm = 0.5 if abs(max_uv[0] - min_uv[0]) < 1e-9 else (u_val - min_uv[0]) / (max_uv[0] - min_uv[0])
            v_norm = 0.5 if abs(max_uv[1] - min_uv[1]) < 1e-9 else (v_val - min_uv[1]) / (max_uv[1] - min_uv[1])
            
            u_norm = max(0.0, min(1.0, u_norm))
            v_norm = max(0.0, min(1.0, v_norm))
            
            result.append((float(u_norm), float(v_norm)))
        
        for i in range(len(self.vertices)):
            self.vertices[i].u = result[i][0]
            self.vertices[i].v = result[i][1]
        return

    def __len__(self):
        return len(self.vertices)

    def __iter__(self):
        return iter(self.vertices)

    def __getitem__(self, index):
        return self.vertices[index]

class Object:
    def __init__(self, polies: List[Polygon] = [], has_uv: bool = False):
        self.polygons = polies.copy()
        self.texture = None;
        self.has_uv_coordinats = has_uv

    def add_face(self, p: Polygon):
        self.polygons.append(p)

    def get_center(self) -> Point:
        all_vertices = []
        unique_vertices = set()
        for poly in self.polygons:
            for vertex in poly.vertices:
                unique_vertices.add(vertex)

        if not unique_vertices:
            return Point(0, 0, 0)

        all_vertices = list(unique_vertices)
        cx = sum(v.x for v in all_vertices) / len(all_vertices)
        cy = sum(v.y for v in all_vertices) / len(all_vertices)
        cz = sum(v.z for v in all_vertices) / len(all_vertices)
        return Point(cx, cy, cz)

    def apply_transformation(self, matrix: np.ndarray):
        unique_vertices = set()
        for poly in self.polygons:
            for vertex in poly.vertices:
                unique_vertices.add(vertex)

        for vertex in unique_vertices:
            h = vertex.to_homogeneous()
            transformed = np.dot(matrix, h)
            vertex.from_homogeneous(transformed)

    def calculate_texture_coordinats(self):
        self.has_uv_coordinats = True
        for poly in self.polygons:
            poly.calculate_texture_coordinats()


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
    # Важно задавать вершины в одном порядке (например, по часовой стрелке),
    # чтобы начальное направление нормалей было консистентным.
    cube = Object([
        Polygon([points[0], points[3], points[2], points[1]]), # Низ
        Polygon([points[0], points[1], points[5], points[4]]), # Передняя
        Polygon([points[1], points[2], points[6], points[5]]), # Правая
        Polygon([points[2], points[3], points[7], points[6]]), # Задняя
        Polygon([points[3], points[0], points[4], points[7]]), # Левая
        Polygon([points[4], points[5], points[6], points[7]])  # Верх
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
    # Задаем грани с консистентным обходом
    octa.add_face(Polygon([vert[1], vert[2], vert[5]]))
    octa.add_face(Polygon([vert[2], vert[3], vert[5]]))
    octa.add_face(Polygon([vert[3], vert[4], vert[5]]))
    octa.add_face(Polygon([vert[4], vert[1], vert[5]]))
    octa.add_face(Polygon([vert[2], vert[1], vert[0]]))
    octa.add_face(Polygon([vert[3], vert[2], vert[0]]))
    octa.add_face(Polygon([vert[4], vert[3], vert[0]]))
    octa.add_face(Polygon([vert[1], vert[4], vert[0]]))

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
    phi =  (1 + np.sqrt(5)) / 2;
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
        # [17, 16, 2, 13, 3], # Эта грань дублирует другие, ее можно убрать
        [4, 18, 19, 5, 14],
        [9, 11, 7, 19, 5],
        [18, 19, 7, 15, 6],
        [12, 1, 9, 5, 14],
        [8, 10, 6, 18, 4]
    ]

    for group in face_groups:
        face_vertices = [vert[i] for i in group]
        dodeca.add_face(Polygon(face_vertices))

    return dodeca