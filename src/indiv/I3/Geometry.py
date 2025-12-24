import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import ctypes
import math
import random

# ==============================================================================
# 2. GEOMETRY UTILS (Corrected Trees & Terrain)
# ==============================================================================
class GeometryUtils:
    @staticmethod
    def generate_terrain_from_map(heightmap, width_scale, depth_scale):
        rows, cols = heightmap.shape
        vertices = []
        indices = []

        offset_x = - (cols * width_scale) / 2.0
        offset_z = - (rows * depth_scale) / 2.0

        for r in range(rows):
            for c in range(cols):
                x = c * width_scale + offset_x
                z = r * depth_scale + offset_z
                y = heightmap[r, c] * 5.0 # Height multiplier

                tiling_scale = 100.0
                # UVs (0.0 to 10.0 for tiling)
                u = c / (cols - 1) * tiling_scale
                v = r / (rows - 1) * tiling_scale

                # Normals
                h_l = heightmap[r, max(0, c-1)] * 5.0
                h_r = heightmap[r, min(cols-1, c+1)] * 5.0
                h_d = heightmap[max(0, r-1), c] * 5.0
                h_u = heightmap[min(rows-1, r+1), c] * 5.0
                nx, ny, nz = h_l - h_r, 2.0 * width_scale, h_d - h_u
                l = math.sqrt(nx*nx + ny*ny + nz*nz)

                vertices.extend([x, y, z, nx/l, ny/l, nz/l, u, v])

        # Indices (Fixed tearing issue)
        for r in range(rows - 1):
            for c in range(cols - 1):
                start = r * cols + c
                # Triangle 1
                indices.extend([start, start + 1, start + cols + 1])
                # Triangle 2
                indices.extend([start, start + cols + 1, start + cols])

        return vertices, indices

    @staticmethod
    def generate_sphere(radius, rings, sectors):
        vertices = []
        indices = []
        R = 1.0 / (rings - 1)
        S = 1.0 / (sectors - 1)

        for r in range(rings):
            for s in range(sectors):
                y = math.sin(-math.pi/2 + math.pi * r * R)
                x = math.cos(2 * math.pi * s * S) * math.sin(math.pi * r * R)
                z = math.sin(2 * math.pi * s * S) * math.sin(math.pi * r * R)
                u, v = s * S, r * R
                vertices.extend([x * radius, y * radius, z * radius, x, y, z, u, v])

        for r in range(rings - 1):
            for s in range(sectors - 1):
                cur = r * sectors + s
                nxt = (r + 1) * sectors + s
                indices.extend([cur, nxt, cur + 1])
                indices.extend([cur + 1, nxt, nxt + 1])
        return vertices, indices

    @staticmethod
    def generate_cone(radius, height, segments):
        vertices = []
        indices = []

        # 0: Tip (Normal Up)
        vertices.extend([0.0, height, 0.0, 0.0, 1.0, 0.0, 0.5, 1.0])
        # 1: Base Center (Normal Down)
        vertices.extend([0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.5, 0.5])

        # Generate Rim Vertices (Duplicated for Side and Base normals)
        for i in range(segments + 1):
            angle = 2 * math.pi * i / segments
            x = math.cos(angle) * radius
            z = math.sin(angle) * radius
            u = i / segments
            l = math.sqrt(x*x + height*height + z*z)

            # Side Vertex (Normal angled out)
            vertices.extend([x, 0.0, z, x/l, 0.5, z/l, u, 0.0])

            # Base Vertex (Normal Down)
            vertices.extend([x, 0.0, z, 0.0, -1.0, 0.0, u, 0.0])

        # Indices (Fixed "Hollow Tree" issue)
        # Vertices layout: [Tip(0), Center(1), S0, B0, S1, B1, ... Sn, Bn]
        # We add 2 vertices per loop step.

        for i in range(segments):
            # Calculate indices based on stride of 2
            curr_s = 2 + 2 * i      # Current Side Vertex
            next_s = 2 + 2 * (i+1)  # Next Side Vertex

            curr_b = 2 + 2 * i + 1      # Current Base Vertex
            next_b = 2 + 2 * (i+1) + 1  # Next Base Vertex

            # Side Triangle: Tip -> Next -> Curr
            indices.extend([0, next_s, curr_s])

            # Base Triangle: Center -> Curr -> Next
            indices.extend([1, curr_b, next_b])

        return vertices, indices

    @staticmethod
    def generate_airship_ropes(length, top_spread, bot_spread):
        """
        Генерирует 4 веревки для дирижабля.
        Веревки начинаются не от центра (0,0,0), а чуть ниже, чтобы выходить из-под шара.
        length: длина веревок вниз
        """
        vertices = []
        indices = []

        # Смещение начала веревок вниз, чтобы они касались низа шара, а не центра
        start_y = -1.8  # Подразумевается, что радиус шара ~2.0
        end_y = start_y - length

        # Точки крепления к шару (чуть шире корзины)
        top_points = [
            (-top_spread, start_y, top_spread),
            (top_spread, start_y, top_spread),
            (top_spread, start_y, -top_spread),
            (-top_spread, start_y, -top_spread)
        ]

        # Точки крепления к корзине (углы)
        bot_points = [
            (-bot_spread, end_y, bot_spread),
            (bot_spread, end_y, bot_spread),
            (bot_spread, end_y, -bot_spread),
            (-bot_spread, end_y, -bot_spread)
        ]

        w = 0.03 # Толщина веревки

        idx = 0
        for i in range(4):
            t = top_points[i]
            b = bot_points[i]

            # Строим "палочку" для каждой веревки
            # Front
            vertices.extend([t[0]-w, t[1], t[2], 0,0,1, 0,1])
            vertices.extend([t[0]+w, t[1], t[2], 0,0,1, 1,1])
            vertices.extend([b[0]-w, b[1], b[2], 0,0,1, 0,0])
            vertices.extend([b[0]+w, b[1], b[2], 0,0,1, 1,0])

            # Side
            vertices.extend([t[0], t[1], t[2]-w, 1,0,0, 0,1])
            vertices.extend([t[0], t[1], t[2]+w, 1,0,0, 1,1])
            vertices.extend([b[0], b[1], b[2]-w, 1,0,0, 0,0])
            vertices.extend([b[0], b[1], b[2]+w, 1,0,0, 1,0])

            start = idx * 8
            indices.extend([start+0, start+2, start+1, start+1, start+2, start+3])
            indices.extend([start+4, start+6, start+5, start+5, start+6, start+7])
            idx += 1

        return vertices, indices

    @staticmethod
    def generate_single_string(length):
        """Генерирует одну длинную нитку по центру."""
        vertices = []
        indices = []

        # Нитка начинается чуть ниже центра (радиус шара NPC ~1.5)
        top_y = -1.4
        bot_y = top_y - length
        w = 0.02

        # Просто длинный тонкий прямоугольник (billboard)
        # Face 1
        vertices.extend([-w, top_y, 0, 0,0,1, 0,1])
        vertices.extend([ w, top_y, 0, 0,0,1, 1,1])
        vertices.extend([-w, bot_y, 0, 0,0,1, 0,0])
        vertices.extend([ w, bot_y, 0, 0,0,1, 1,0])

        # Face 2 (перпендикулярно, чтобы видно было сбоку)
        vertices.extend([0, top_y, -w, 1,0,0, 0,1])
        vertices.extend([0, top_y,  w, 1,0,0, 1,1])
        vertices.extend([0, bot_y, -w, 1,0,0, 0,0])
        vertices.extend([0, bot_y,  w, 1,0,0, 1,0])

        indices.extend([0, 2, 1, 1, 2, 3])
        indices.extend([4, 6, 5, 5, 6, 7])

        return vertices, indices

    @staticmethod
    def generate_cylinder(radius, height, segments):
        vertices = []
        indices = []
        for i in range(segments + 1):
            angle = 2 * math.pi * i / segments
            x, z = math.cos(angle) * radius, math.sin(angle) * radius
            u = i / segments
            # Top Rim
            vertices.extend([x, height, z, 0,1,0, u, 1])
            # Top Side
            vertices.extend([x, height, z, x,0,z, u, 1])
            # Bot Side
            vertices.extend([x, 0, z, x,0,z, u, 0])
            # Bot Rim
            vertices.extend([x, 0, z, 0,-1,0, u, 0])

        # Cap Centers
        tc = len(vertices) // 8
        vertices.extend([0, height, 0, 0,1,0, 0.5, 0.5])
        bc = tc + 1
        vertices.extend([0, 0, 0, 0,-1,0, 0.5, 0.5])

        for i in range(segments):
            b = i * 4
            # Caps
            indices.extend([tc, b, b+4])
            indices.extend([bc, b+3+4, b+3])
            # Sides
            indices.extend([b+1, b+5, b+6])
            indices.extend([b+1, b+6, b+2])
        return vertices, indices

    @staticmethod
    def generate_cube_v_i():
        vertices = []
        def add_face(p1, p2, p3, p4, nx, ny, nz):
            vertices.extend(p1 + [nx, ny, nz, 0.0, 0.0])
            vertices.extend(p2 + [nx, ny, nz, 1.0, 0.0])
            vertices.extend(p3 + [nx, ny, nz, 1.0, 1.0])
            vertices.extend(p4 + [nx, ny, nz, 0.0, 1.0])
        p = [[-0.5, -0.5, 0.5], [0.5, -0.5, 0.5], [0.5, 0.5, 0.5], [-0.5, 0.5, 0.5],
             [-0.5, -0.5, -0.5], [0.5, -0.5, -0.5], [0.5, 0.5, -0.5], [-0.5, 0.5, -0.5]]

        # Normals: Front, Back, Left, Right, Top, Bottom
        add_face(p[0], p[1], p[2], p[3], 0, 0, 1)
        add_face(p[5], p[4], p[7], p[6], 0, 0, -1)
        add_face(p[4], p[0], p[3], p[7], -1, 0, 0)
        add_face(p[1], p[5], p[6], p[2], 1, 0, 0)
        add_face(p[3], p[2], p[6], p[7], 0, 1, 0)
        add_face(p[4], p[5], p[1], p[0], 0, -1, 0)

        indices = []
        for i in range(6):
            b = i * 4
            indices.extend([b, b+1, b+2, b+2, b+3, b])
        return vertices, indices

    @staticmethod
    def generate_pyramid(base_size, height):
        hs = base_size / 2.0
        vertices = []
        # Base (square)
        vertices.extend([-hs, 0, hs, 0,-1,0, 0,0])
        vertices.extend([hs, 0, hs, 0,-1,0, 1,0])
        vertices.extend([hs, 0, -hs, 0,-1,0, 1,1])
        vertices.extend([-hs, 0, -hs, 0,-1,0, 0,1])

        # Sides (Triangles)
        # Front
        vertices.extend([-hs,0,hs, 0,0.5,0.8, 0,0]); vertices.extend([hs,0,hs, 0,0.5,0.8, 1,0]); vertices.extend([0,height,0, 0,0.5,0.8, 0.5,1])
        # Right
        vertices.extend([hs,0,hs, 0.8,0.5,0, 0,0]); vertices.extend([hs,0,-hs, 0.8,0.5,0, 1,0]); vertices.extend([0,height,0, 0.8,0.5,0, 0.5,1])
        # Back
        vertices.extend([hs,0,-hs, 0,0.5,-0.8, 0,0]); vertices.extend([-hs,0,-hs, 0,0.5,-0.8, 1,0]); vertices.extend([0,height,0, 0,0.5,-0.8, 0.5,1])
        # Left
        vertices.extend([-hs,0,-hs, -0.8,0.5,0, 0,0]); vertices.extend([-hs,0,hs, -0.8,0.5,0, 1,0]); vertices.extend([0,height,0, -0.8,0.5,0, 0.5,1])

        indices = [0, 1, 2, 0, 2, 3] # Base
        indices.extend([4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]) # Sides
        return vertices, indices

    @staticmethod
    def load_obj(filename, swap_yz=False):
        """
        Загружает OBJ файл.
        swap_yz: Если модель лежит на боку (частая проблема экспорта), ставим True.
        """
        vertices = []
        indices = []

        # Временные списки для данных из файла
        v_data = [] # Вершины
        vt_data = [] # Текстурные координаты
        vn_data = [] # Нормали

        final_vertices = []

        # Словарь для избежания дубликатов вершин (оптимизация)
        # vertex_str -> index
        unique_verts = {}
        idx_counter = 0

        try:
            with open(filename, 'r') as f:
                for line in f:
                    if line.startswith('#'): continue
                    vals = line.split()
                    if not vals: continue

                    if vals[0] == 'v':
                        x, y, z = float(vals[1]), float(vals[2]), float(vals[3])
                        if swap_yz:
                            v_data.append([x, z, -y]) # Поворот осей
                        else:
                            v_data.append([x, y, z])

                    elif vals[0] == 'vt':
                        vt_data.append([float(vals[1]), float(vals[2])])

                    elif vals[0] == 'vn':
                        nx, ny, nz = float(vals[1]), float(vals[2]), float(vals[3])
                        if swap_yz:
                            vn_data.append([nx, nz, -ny])
                        else:
                            vn_data.append([nx, ny, nz])

                    elif vals[0] == 'f':
                        # Обрабатываем грани (обычно треугольники)
                        # Формат f v/vt/vn v/vt/vn v/vt/vn
                        for i in range(1, 4):
                            w = vals[i].split('/')

                            # Индексы в OBJ начинаются с 1, поэтому -1
                            vi = int(w[0]) - 1
                            vti = int(w[1]) - 1 if len(w) > 1 and w[1] else 0
                            vni = int(w[2]) - 1 if len(w) > 2 and w[2] else 0

                            # Ключ для уникальности
                            key = (vi, vti, vni)

                            if key not in unique_verts:
                                unique_verts[key] = idx_counter
                                idx_counter += 1

                                # Собираем [x, y, z, nx, ny, nz, u, v]
                                pos = v_data[vi]
                                tex = vt_data[vti] if vt_data and vti < len(vt_data) else [0.0, 0.0]
                                norm = vn_data[vni] if vn_data and vni < len(vn_data) else [0.0, 1.0, 0.0]

                                final_vertices.extend(pos + norm + tex)

                            indices.append(unique_verts[key])

            return final_vertices, indices

        except Exception as e:
            print(f"Failed to load OBJ {filename}: {e}")
            return GeometryUtils.generate_cube_v_i() # Fallback