import numpy as np
from primitives import *

# ===== Матрицы преобразований =====

def translation_matrix(dx: float, dy: float, dz: float) -> np.ndarray:
    """Матрица переноса"""
    return np.array([
        [1, 0, 0, dx],
        [0, 1, 0, dy],
        [0, 0, 1, dz],
        [0, 0, 0, 1]
    ])


def scale_matrix(sx: float, sy: float, sz: float) -> np.ndarray:
    """Матрица масштабирования"""
    return np.array([
        [sx, 0, 0, 0],
        [0, sy, 0, 0],
        [0, 0, sz, 0],
        [0, 0, 0, 1]
    ])


def rotation_x_matrix(angle: float) -> np.ndarray:
    """Матрица поворота вокруг оси X"""
    c = np.cos(angle)
    s = np.sin(angle)
    return np.array([
        [1, 0, 0, 0],
        [0, c, -s, 0],
        [0, s, c, 0],
        [0, 0, 0, 1]
    ])


def rotation_y_matrix(angle: float) -> np.ndarray:
    """Матрица поворота вокруг оси Y"""
    c = np.cos(angle)
    s = np.sin(angle)
    return np.array([
        [c, 0, s, 0],
        [0, 1, 0, 0],
        [-s, 0, c, 0],
        [0, 0, 0, 1]
    ])


def rotation_z_matrix(angle: float) -> np.ndarray:
    """Матрица поворота вокруг оси Z"""
    c = np.cos(angle)
    s = np.sin(angle)
    return np.array([
        [c, -s, 0, 0],
        [s, c, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ])


def reflection_xy_matrix() -> np.ndarray:
    """Отражение относительно плоскости XY"""
    return np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, -1, 0],
        [0, 0, 0, 1]
    ])


def reflection_xz_matrix() -> np.ndarray:
    """Отражение относительно плоскости XZ"""
    return np.array([
        [1, 0, 0, 0],
        [0, -1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ])


def reflection_yz_matrix() -> np.ndarray:
    """Отражение относительно плоскости YZ"""
    return np.array([
        [-1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ])


def scale_relative_to_center(obj: Object, sx: float, sy: float, sz: float):
    """Масштабирование относительно центра объекта"""
    center = obj.get_center()

    # Перенос в начало координат
    t1 = translation_matrix(-center.x, -center.y, -center.z)
    # Масштабирование
    s = scale_matrix(sx, sy, sz)
    # Перенос обратно
    t2 = translation_matrix(center.x, center.y, center.z)

    # Комбинированная матрица
    matrix = np.dot(t2, np.dot(s, t1))
    obj.apply_transformation(matrix)


def rotate_around_center(obj: Object, axis: str, angle: float):
    """Вращение вокруг центра объекта"""
    center = obj.get_center()

    t1 = translation_matrix(-center.x, -center.y, -center.z)

    if axis == 'X':
        r = rotation_x_matrix(angle)
    elif axis == 'Y':
        r = rotation_y_matrix(angle)
    else:  # Z
        r = rotation_z_matrix(angle)

    t2 = translation_matrix(center.x, center.y, center.z)

    matrix = np.dot(t2, np.dot(r, t1))

    obj.apply_transformation(matrix)



def rotate_around_line(obj: Object, p1: Point, p2: Point, angle: float):
    """Поворот вокруг произвольной прямой"""
    # Вектор направления прямой
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    dz = p2.z - p1.z

    # Нормализация
    length = np.sqrt(dx * dx + dy * dy + dz * dz)
    if length < 1e-6:
        return

    dx /= length
    dy /= length
    dz /= length

    # Перенос точки p1 в начало координат
    t1 = translation_matrix(-p1.x, -p1.y, -p1.z)

    # Поворот вокруг оси, заданной направляющим вектором (dx, dy, dz)
    # Используем формулу Родрига
    c = np.cos(angle)
    s = np.sin(angle)
    t = 1 - c

    rotation = np.array([
        [t * dx * dx + c, t * dx * dy - s * dz, t * dx * dz + s * dy, 0],
        [t * dx * dy + s * dz, t * dy * dy + c, t * dy * dz - s * dx, 0],
        [t * dx * dz - s * dy, t * dy * dz + s * dx, t * dz * dz + c, 0],
        [0, 0, 0, 1]
    ])

    # Перенос обратно
    t2 = translation_matrix(p1.x, p1.y, p1.z)

    matrix = np.dot(t2, np.dot(rotation, t1))
    obj.apply_transformation(matrix)