import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import ctypes
import math
import random

# ==============================================================================
# 5. MESH CLASS
# ==============================================================================
class Mesh:
    def __init__(self, vertices, indices):
        self.vertices = np.array(vertices, dtype=np.float32)
        self.indices = np.array(indices, dtype=np.uint32)
        self.index_count = len(self.indices)
        self.instance_count = 0

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

        self.ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)

        stride = 32
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(24))

        self.instance_vbo = glGenBuffers(1)
        glBindVertexArray(0)

    def init_instancing(self, model_matrices):
        self.instance_count = len(model_matrices)
        data = np.array(model_matrices, dtype=np.float32).transpose(0, 2, 1).flatten()
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.instance_vbo)
        glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)
        stride = 64
        for i in range(4):
            glEnableVertexAttribArray(3+i)
            glVertexAttribPointer(3+i, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(i*16))
            glVertexAttribDivisor(3+i, 1)
        glBindVertexArray(0)

    def draw(self, shader):
        shader.set_bool("isInstanced", False)
        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

    def draw_instanced(self, shader):
        if self.instance_count == 0: return
        shader.set_bool("isInstanced", True)
        glBindVertexArray(self.vao)
        glDrawElementsInstanced(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, None, self.instance_count)
        glBindVertexArray(0)

    def destroy(self):
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(3, (self.vbo, self.ebo, self.instance_vbo))