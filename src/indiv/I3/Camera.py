import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import ctypes
import math
import random

# ==============================================================================
# 3. CAMERA CLASS
# ==============================================================================
class Camera:
    def __init__(self, position):
        self.position = np.array(position, dtype=np.float32)
        self.yaw = -90.0
        self.pitch = -20.0
        self.fov = 70.0
        self.front = np.array([0.0, 0.0, -1.0], dtype=np.float32)
        self.up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        self.update_vectors()

    def update_vectors(self):
        rad_yaw = np.radians(self.yaw)
        rad_pitch = np.radians(self.pitch)
        front = np.array([
            np.cos(rad_yaw) * np.cos(rad_pitch),
            np.sin(rad_pitch),
            np.sin(rad_yaw) * np.cos(rad_pitch)
        ], dtype=np.float32)
        self.front = front / np.linalg.norm(front)
        right = np.cross(self.front, [0, 1, 0])
        self.up = np.cross(right, self.front)

    def follow(self, target_pos, target_yaw, distance=10.0, height=5.0):
        rad_yaw = np.radians(target_yaw)
        back_x = -np.cos(rad_yaw)
        back_z = -np.sin(rad_yaw)

        self.position[0] = target_pos[0] + back_x * distance
        self.position[1] = target_pos[1] + height
        self.position[2] = target_pos[2] + back_z * distance

        direction = target_pos - self.position
        direction[1] -= 2.0
        self.front = direction / np.linalg.norm(direction)
        right = np.cross(self.front, [0,1,0])
        self.up = np.cross(right, self.front)

    def get_view_matrix(self):
        f, u = self.front, self.up
        s = np.cross(f, u)
        s /= np.linalg.norm(s)
        rotation = np.identity(4, dtype=np.float32)
        rotation[0, :3] = s
        rotation[1, :3] = u
        rotation[2, :3] = -f
        translation = np.identity(4, dtype=np.float32)
        translation[:3, 3] = -self.position
        return np.dot(rotation, translation)

    def get_projection_matrix(self, w, h):
        aspect = w / h if h != 0 else 1
        tan_hf = np.tan(np.radians(self.fov) / 2.0)
        zn, zf = 0.1, 150.0
        proj = np.zeros((4, 4), dtype=np.float32)
        proj[0, 0] = 1.0 / (aspect * tan_hf)
        proj[1, 1] = 1.0 / tan_hf
        proj[2, 2] = -(zf + zn) / (zf - zn)
        proj[2, 3] = -(2.0 * zf * zn) / (zf - zn)
        proj[3, 2] = -1.0
        return proj