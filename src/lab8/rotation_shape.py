import pygame
from primitives import *
from create_test_models import *
from datetime import datetime
from object_IO import *
from D3Renderer import *
import os
import math
from plot import Plot
import re

test_string = "(0, 0) (100, 100) (150, 50) (200, 100)"  # тестовая строка

# ===== ТОчки из строки =====

def get_dots_from_string(coords_string=test_string):
    pattern = r'\(([^,]+),([^)]+)\)'
    matches = re.findall(pattern, coords_string)
    
    points = []
    for x_str, y_str in matches:
        x = float(x_str.strip())
        y = float(y_str.strip())
        points.append([x, y])
    
    return points

# ====== Создание фигуры вращения

def create_solid_of_revolution(dots, iterations):
    obj = Object()

    vertices = []
    for d in dots:
        vertices.append(Point(d[0], d[1], 0))

    vertices_1 = vertices.copy()
    for i in range(iterations):
        vertices_2 = []
        angle = np.radians(360*(i+1) / iterations)
        for v in vertices:
            vertices_2.append(Point(v.x, v.y*np.cos(angle), v.y*np.sin(angle)))

        for j in range(len(vertices)-1):
            obj.add_face(Polygon([vertices_1[j], vertices_1[j+1], vertices_2[j+1], vertices_2[j]]))
        vertices_1 = vertices_2

    return obj
