"""Матрицы аффинных преобразований"""
import numpy as np
import math


def translation_matrix(dx: float, dy: float) -> np.ndarray:
    """
    Матрица смещения на (dx, dy)
    """
    return np.array([
        [1, 0, dx],
        [0, 1, dy],
        [0, 0, 1]
    ])


def rotation_matrix(angle: float, cx: float, cy: float) -> np.ndarray:
    """
    Матрица поворота на угол angle (в радианах) вокруг точки (cx, cy)
    Формула: T(cx,cy) * R(angle) * T(-cx,-cy)
    """
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    return np.array([
        [cos_a, -sin_a, -cx * cos_a + cy * sin_a + cx],
        [sin_a, cos_a, -cx * sin_a - cy * cos_a + cy],
        [0, 0, 1]
    ])


def scaling_matrix(sx: float, sy: float, cx: float, cy: float) -> np.ndarray:
    """
    Матрица масштабирования с коэффициентами (sx, sy)
    относительно точки (cx, cy)
    Формула: T(cx,cy) * S(sx,sy) * T(-cx,-cy)
    """
    return np.array([
        [sx, 0, cx * (1 - sx)],
        [0, sy, cy * (1 - sy)],
        [0, 0, 1]
    ])