import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import ctypes
import math
import random
import time

# ==============================================================================
# 0. UI & HELPER CLASSES
# ==============================================================================
class UIRenderer:
    """Handles 2D rendering (Text, Buttons) over 3D scene."""
    def __init__(self, width, height):
        self.width = width
        self.height = height

        # Simple shader for 2D textures (UI)
        self.vs = """
        #version 330 core
        layout (location = 0) in vec2 aPos;
        layout (location = 1) in vec2 aTexCoord;
        out vec2 TexCoord;
        uniform mat4 projection;
        uniform mat4 model;
        void main() {
            gl_Position = projection * model * vec4(aPos, 0.0, 1.0);
            TexCoord = aTexCoord;
        }
        """
        self.fs = """
        #version 330 core
        in vec2 TexCoord;
        out vec4 FragColor;
        uniform sampler2D textTexture;
        uniform vec3 color;
        uniform bool useTexture;

        void main() {
            if (useTexture) {
                vec4 sampled = texture(textTexture, TexCoord);
                FragColor = vec4(color, 1.0) * sampled;
            } else {
                FragColor = vec4(color, 1.0);
            }
        }
        """
        self.shader = compileProgram(compileShader(self.vs, GL_VERTEX_SHADER),
                                     compileShader(self.fs, GL_FRAGMENT_SHADER))

        # Quad Geometry
        # x, y, u, v
        self.vertices = np.array([
            0.0, 1.0, 0.0, 1.0,
            1.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 0.0,

            0.0, 1.0, 0.0, 1.0,
            1.0, 1.0, 1.0, 1.0,
            1.0, 0.0, 1.0, 0.0
        ], dtype=np.float32)

        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(8))
        glBindVertexArray(0)

        self.font = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 20)

    def text_to_texture(self, text, color=(255, 255, 255), font_scale=1.0):
        font = self.font if font_scale >= 1.0 else self.font_small
        surf = font.render(text, True, color)
        data = pygame.image.tostring(surf, "RGBA", False)
        w, h = surf.get_width(), surf.get_height()

        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        return tex_id, w, h

    def draw_text(self, text, x, y, color=(1, 1, 1), font_scale=1.0):
        tex_id, w, h = self.text_to_texture(text, (255, 255, 255), font_scale)
        self.draw_texture(tex_id, x, y, w, h, color)
        glDeleteTextures(1, [tex_id])

    def draw_texture(self, tex_id, x, y, w, h, color=(1, 1, 1)):
        glUseProgram(self.shader)

        proj = np.array([
            [2/self.width, 0, 0, 0],
            [0, -2/self.height, 0, 0],
            [0, 0, -1, 0],
            [-1, 1, 0, 1]
        ], dtype=np.float32)

        model = np.array([
            [w, 0, 0, 0],
            [0, h, 0, 0],
            [0, 0, 1, 0],
            [x, y, 0, 1]
        ], dtype=np.float32)

        glUniformMatrix4fv(glGetUniformLocation(self.shader, "projection"), 1, GL_FALSE, proj)
        glUniformMatrix4fv(glGetUniformLocation(self.shader, "model"), 1, GL_FALSE, model)
        glUniform3f(glGetUniformLocation(self.shader, "color"), color[0], color[1], color[2])
        glUniform1i(glGetUniformLocation(self.shader, "useTexture"), 1)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, tex_id)

        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)

    def draw_rect(self, x, y, w, h, color=(0.5, 0.5, 0.5)):
        """Draws a solid rectangle (for buttons)"""
        glUseProgram(self.shader)
        proj = np.array([
            [2/self.width, 0, 0, 0],
            [0, -2/self.height, 0, 0],
            [0, 0, -1, 0],
            [-1, 1, 0, 1]
        ], dtype=np.float32)
        model = np.array([
            [w, 0, 0, 0],
            [0, h, 0, 0],
            [0, 0, 1, 0],
            [x, y, 0, 1]
        ], dtype=np.float32)

        glUniformMatrix4fv(glGetUniformLocation(self.shader, "projection"), 1, GL_FALSE, proj)
        glUniformMatrix4fv(glGetUniformLocation(self.shader, "model"), 1, GL_FALSE, model)
        glUniform3f(glGetUniformLocation(self.shader, "color"), color[0], color[1], color[2])
        glUniform1i(glGetUniformLocation(self.shader, "useTexture"), 0)

        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)