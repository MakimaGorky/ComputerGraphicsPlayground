import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import ctypes
import math
import random
import time

from Texture import *
from Geometry import *
from Camera import *
from Shader import *
from Mesh import *

# ==============================================================================
# 0. UI & HELPER CLASSES (NEW)
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

# ==============================================================================
# 1. TEXTURE & HEIGHTMAP UTILS
# ==============================================================================
class TextureUtils:
    @staticmethod
    def generate_checkerboard(width, height, color1=(255, 255, 255), color2=(0, 0, 0)):
        arr = np.zeros((height, width, 3), dtype=np.uint8)
        block_w = width // 8
        block_h = height // 8
        for y in range(height):
            for x in range(width):
                if ((x // block_w) + (y // block_h)) % 2 == 0:
                    arr[y, x] = color1
                else:
                    arr[y, x] = color2
        return arr

    @staticmethod
    def generate_noise_texture(width, height, color_base=(50, 150, 50)):
        arr = np.random.randint(0, 40, (height, width, 3), dtype=np.int16)
        base = np.array(color_base, dtype=np.int16)
        return np.clip(base + arr, 0, 255).astype(np.uint8)

    @staticmethod
    def load_heightmap_from_image(filepath, width, depth):
        try:
            print(f"Loading heightmap from {filepath}...")
            surf = pygame.image.load(filepath)
            surf = pygame.transform.scale(surf, (width, depth))
            rgb_array = pygame.surfarray.array3d(surf)
            grayscale = np.mean(rgb_array, axis=2).T
            height_data = (grayscale / 255.0) * 2.0
            return height_data.astype(np.float32)
        except Exception as e:
            print(f"Heightmap load failed: {e}. Using procedural.")
            return TextureUtils.generate_heightmap(width, depth)

    @staticmethod
    def generate_heightmap(width, depth):
        data = np.random.rand(depth, width) * 2.0
        for _ in range(16):
            data[1:-1, 1:-1] = (
                data[:-2, 1:-1] + data[2:, 1:-1] +
                data[1:-1, :-2] + data[1:-1, 2:] +
                data[1:-1, 1:-1] * 4
            ) / 8.0
        return data.astype(np.float32)

    @staticmethod
    def create_house_lightmap():
        size = 128
        lightmap = np.ones((size, size, 3), dtype=np.float32)
        shadow_color = np.array([0.4, 0.5, 0.7], dtype=np.float32)
        light_color = np.array([1.0, 0.95, 0.85], dtype=np.float32)

        for y in range(size):
            progress = y / size
            shadow_strength = np.power(progress, 2.0)
            for x in range(size):
                color = light_color * (1 - shadow_strength) + shadow_color * shadow_strength
                edge_dist = min(x, size - x, y, size - y) / (size / 2)
                ao = 0.5 + 0.5 * min(1.0, edge_dist * 2.0)
                lightmap[y, x] = color * ao

        for _ in range(3):
            temp = lightmap.copy()
            for y in range(1, size - 1):
                for x in range(1, size - 1):
                    lightmap[y, x] = temp[y-1:y+2, x-1:x+2].mean(axis=(0, 1))

        lightmap = np.clip(lightmap, 0.0, 1.0)
        return (lightmap * 255).astype(np.uint8)

class Texture:
    def __init__(self, filepath=None, texture_type='diffuse', gen_color=None, custom_array=None):
        self.texture_id = glGenTextures(1)
        self.type = texture_type

        data = None
        width, height = 64, 64
        loaded = False

        if filepath:
            try:
                surf = pygame.image.load(filepath)
                surf = pygame.transform.flip(surf, False, True)
                data = pygame.image.tostring(surf, "RGB", 1)
                width, height = surf.get_width(), surf.get_height()
                loaded = True
            except:
                pass

        if not loaded:
            if custom_array is not None:
                array_data = custom_array
            elif gen_color:
                array_data = TextureUtils.generate_noise_texture(64, 64, gen_color)
            else:
                array_data = TextureUtils.generate_checkerboard(64, 64)
            width, height = array_data.shape[1], array_data.shape[0]
            data = array_data.tobytes()

        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, data)
        glGenerateMipmap(GL_TEXTURE_2D)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)

    def bind(self, unit=0):
        glActiveTexture(GL_TEXTURE0 + unit)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)

# ==============================================================================
# 2. GEOMETRY UTILS
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
                y = heightmap[r, c] * 5.0
                u = c / (cols - 1) * 10.0
                v = r / (rows - 1) * 10.0

                h_l = heightmap[r, max(0, c-1)] * 5.0
                h_r = heightmap[r, min(cols-1, c+1)] * 5.0
                h_d = heightmap[max(0, r-1), c] * 5.0
                h_u = heightmap[min(rows-1, r+1), c] * 5.0
                nx, ny, nz = h_l - h_r, 2.0 * width_scale, h_d - h_u
                l = math.sqrt(nx*nx + ny*ny + nz*nz)
                vertices.extend([x, y, z, nx/l, ny/l, nz/l, u, v])

        for r in range(rows - 1):
            for c in range(cols - 1):
                start = r * cols + c
                indices.extend([start, start + 1, start + cols + 1])
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
        vertices.extend([0.0, height, 0.0, 0.0, 1.0, 0.0, 0.5, 1.0])
        vertices.extend([0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.5, 0.5])
        for i in range(segments + 1):
            angle = 2 * math.pi * i / segments
            x = math.cos(angle) * radius
            z = math.sin(angle) * radius
            u = i / segments
            l = math.sqrt(x*x + height*height + z*z)
            vertices.extend([x, 0.0, z, x/l, 0.5, z/l, u, 0.0])
            vertices.extend([x, 0.0, z, 0.0, -1.0, 0.0, u, 0.0])
        for i in range(segments):
            curr_s = 2 + 2 * i
            next_s = 2 + 2 * (i+1)
            curr_b = 2 + 2 * i + 1
            next_b = 2 + 2 * (i+1) + 1
            indices.extend([0, next_s, curr_s])
            indices.extend([1, curr_b, next_b])
        return vertices, indices

    @staticmethod
    def generate_airship_ropes(length, top_spread, bot_spread):
        vertices = []
        indices = []
        start_y = -1.8
        end_y = start_y - length
        top_points = [(-top_spread, start_y, top_spread), (top_spread, start_y, top_spread),
                      (top_spread, start_y, -top_spread), (-top_spread, start_y, -top_spread)]
        bot_points = [(-bot_spread, end_y, bot_spread), (bot_spread, end_y, bot_spread),
                      (bot_spread, end_y, -bot_spread), (-bot_spread, end_y, -bot_spread)]
        w = 0.03
        idx = 0
        for i in range(4):
            t = top_points[i]; b = bot_points[i]
            vertices.extend([t[0]-w, t[1], t[2], 0,0,1, 0,1])
            vertices.extend([t[0]+w, t[1], t[2], 0,0,1, 1,1])
            vertices.extend([b[0]-w, b[1], b[2], 0,0,1, 0,0])
            vertices.extend([b[0]+w, b[1], b[2], 0,0,1, 1,0])
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
        vertices = []
        indices = []
        top_y = -1.4; bot_y = top_y - length; w = 0.02
        vertices.extend([-w, top_y, 0, 0,0,1, 0,1]); vertices.extend([ w, top_y, 0, 0,0,1, 1,1])
        vertices.extend([-w, bot_y, 0, 0,0,1, 0,0]); vertices.extend([ w, bot_y, 0, 0,0,1, 1,0])
        vertices.extend([0, top_y, -w, 1,0,0, 0,1]); vertices.extend([0, top_y,  w, 1,0,0, 1,1])
        vertices.extend([0, bot_y, -w, 1,0,0, 0,0]); vertices.extend([0, bot_y,  w, 1,0,0, 1,0])
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
            vertices.extend([x, height, z, 0,1,0, u, 1])
            vertices.extend([x, height, z, x,0,z, u, 1])
            vertices.extend([x, 0, z, x,0,z, u, 0])
            vertices.extend([x, 0, z, 0,-1,0, u, 0])
        tc = len(vertices) // 8
        vertices.extend([0, height, 0, 0,1,0, 0.5, 0.5])
        bc = tc + 1
        vertices.extend([0, 0, 0, 0,-1,0, 0.5, 0.5])
        for i in range(segments):
            b = i * 4
            indices.extend([tc, b, b+4]); indices.extend([bc, b+3+4, b+3])
            indices.extend([b+1, b+5, b+6]); indices.extend([b+1, b+6, b+2])
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
        vertices.extend([-hs, 0, hs, 0,-1,0, 0,0]); vertices.extend([hs, 0, hs, 0,-1,0, 1,0])
        vertices.extend([hs, 0, -hs, 0,-1,0, 1,1]); vertices.extend([-hs, 0, -hs, 0,-1,0, 0,1])
        vertices.extend([-hs,0,hs, 0,0.5,0.8, 0,0]); vertices.extend([hs,0,hs, 0,0.5,0.8, 1,0]); vertices.extend([0,height,0, 0,0.5,0.8, 0.5,1])
        vertices.extend([hs,0,hs, 0.8,0.5,0, 0,0]); vertices.extend([hs,0,-hs, 0.8,0.5,0, 1,0]); vertices.extend([0,height,0, 0.8,0.5,0, 0.5,1])
        vertices.extend([hs,0,-hs, 0,0.5,-0.8, 0,0]); vertices.extend([-hs,0,-hs, 0,0.5,-0.8, 1,0]); vertices.extend([0,height,0, 0,0.5,-0.8, 0.5,1])
        vertices.extend([-hs,0,-hs, -0.8,0.5,0, 0,0]); vertices.extend([-hs,0,hs, -0.8,0.5,0, 1,0]); vertices.extend([0,height,0, -0.8,0.5,0, 0.5,1])
        indices = [0, 1, 2, 0, 2, 3]
        indices.extend([4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
        return vertices, indices

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
        rotation[0, :3] = s; rotation[1, :3] = u; rotation[2, :3] = -f
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

# ==============================================================================
# 4. SHADER CLASS
# ==============================================================================
class Shader:
    def __init__(self, vs_src, fs_src):
        self.program = compileProgram(
            compileShader(vs_src, GL_VERTEX_SHADER),
            compileShader(fs_src, GL_FRAGMENT_SHADER)
        )
    def use(self): glUseProgram(self.program)
    def set_mat4(self, name, mat): glUniformMatrix4fv(glGetUniformLocation(self.program, name), 1, GL_TRUE, mat)
    def set_vec3(self, name, x, y=None, z=None):
        if y is None: glUniform3fv(glGetUniformLocation(self.program, name), 1, x)
        else: glUniform3f(glGetUniformLocation(self.program, name), x, y, z)
    def set_float(self, name, val): glUniform1f(glGetUniformLocation(self.program, name), val)
    def set_bool(self, name, val): glUniform1i(glGetUniformLocation(self.program, name), int(val))
    def set_int(self, name, val): glUniform1i(glGetUniformLocation(self.program, name), val)
    def destroy(self): glDeleteProgram(self.program)

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
        if self.instance_count == 0: return
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

    def update_instancing(self, model_matrices):
        """Updates instance data dynamically"""
        self.instance_count = len(model_matrices)
        if self.instance_count == 0: return
        data = np.array(model_matrices, dtype=np.float32).transpose(0, 2, 1).flatten()
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.instance_vbo)
        glBufferSubData(GL_ARRAY_BUFFER, 0, data.nbytes, data)
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

# ==============================================================================
# 6. APP CLASS (Game Logic & UI)
# ==============================================================================
class App:
    STATE_MENU = 0
    STATE_GAME = 1
    STATE_SETTINGS = 2
    STATE_WIN = 3

    def __init__(self):
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        self.width, self.height = 1000, 800
        pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Airship Delivery")
        self.clock = pygame.time.Clock()
        self.running = True

        # State
        self.state = self.STATE_MENU
        self.use_procedural_map = True
        self.map_width, self.map_depth = 600, 600

        # UI
        self.ui = UIRenderer(self.width, self.height)

        # 3D Init
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Resources
        self.setup_terrain_data()
        self.setup_textures()
        self.setup_shaders()
        self.setup_geometry()

        # Game Objects
        self.airship_pos = np.array([0.0, 16.0, 0.0], dtype=np.float32)
        self.airship_yaw = -90.0
        self.camera = Camera(position=[0, 10, 20])

        self.reset_game()

    def reset_game(self):
        """Resets game state"""
        self.airship_pos = np.array([0.0, 16.0, 0.0], dtype=np.float32)
        self.airship_yaw = -90.0
        self.packages = []
        self.score = 0
        self.game_time = 0.0
        self.game_finished = False

        self.setup_scene_instances()
        self.setup_npcs()
        self.clouds = self.create_clouds(15)
        self.spotlight_active = True

    def setup_terrain_data(self):
        if self.use_procedural_map:
            print("Using Procedural Terrain")
            self.heightmap_data = TextureUtils.generate_heightmap(self.map_width, self.map_depth)
        else:
            print("Attempting to load File Terrain")
            self.heightmap_data = TextureUtils.load_heightmap_from_image(
                "assets/heightmap.png", self.map_width, self.map_depth
            )

    def reload_terrain(self):
        self.setup_terrain_data()
        # Re-generate terrain mesh
        self.terrain_mesh.destroy()
        t_v, t_i = GeometryUtils.generate_terrain_from_map(self.heightmap_data, 1.0, 1.0)
        self.terrain_mesh = Mesh(t_v, t_i)
        self.reset_game()

    def setup_textures(self):
        self.tex_grass = Texture("assets/grass.jpg", gen_color=(30, 100, 30))
        self.tex_dirt = Texture("assets/dirt.jpg", gen_color=(100, 80, 50))
        self.tex_wood = Texture("assets/wood.jpg", gen_color=(139, 69, 19))
        self.tex_metal = Texture("assets/metal.jpg", gen_color=(150, 150, 160))
        self.tex_leaf = Texture("assets/leaf.jpg", gen_color=(20, 80, 20))
        self.tex_balloon = Texture("assets/cloth.jpg", gen_color=(200, 50, 50))
        self.tex_white = Texture(None, gen_color=(255, 255, 255))
        self.tex_black = Texture(None, gen_color=(0,0,0))

        self.tex_window_emissive = self.create_window()
        self.tex_house_lightmap = Texture(None, texture_type='lightmap', custom_array=TextureUtils.create_house_lightmap())

    def create_window(self):
        arr = np.zeros((64, 64, 3), dtype=np.uint8)
        arr[20:30, 25:35] = [255, 255, 100] # Window
        return Texture(None, 'lightmap', gen_color=None, custom_array=arr)

    def setup_shaders(self):
        vs = """
        #version 330 core
        layout (location = 0) in vec3 aPos;
        layout (location = 1) in vec3 aNormal;
        layout (location = 2) in vec2 aTexCoord;
        layout (location = 3) in mat4 aInstanceMatrix;
        out vec3 FragPos; out vec3 Normal; out vec2 TexCoord;
        uniform mat4 model; uniform mat4 view; uniform mat4 projection; uniform bool isInstanced;
        void main() {
            mat4 currentModel = isInstanced ? aInstanceMatrix : model;
            FragPos = vec3(currentModel * vec4(aPos, 1.0));
            Normal = mat3(transpose(inverse(currentModel))) * aNormal;
            TexCoord = aTexCoord;
            gl_Position = projection * view * vec4(FragPos, 1.0);
        }
        """
        fs = """
        #version 330 core
        out vec4 FragColor;
        in vec3 FragPos; in vec3 Normal; in vec2 TexCoord;
        uniform vec3 viewPos; uniform float alpha; uniform vec3 emissiveColor;
        uniform sampler2D diffuseMap; uniform sampler2D emissiveMap; uniform sampler2D lightMap;
        uniform bool useEmissive; uniform bool useLightMap; uniform vec3 tintColor;
        uniform vec3 spotPos; uniform vec3 spotDir; uniform float spotCutoff;

        void main() {
            vec4 texColor = texture(diffuseMap, TexCoord) * vec4(tintColor, 1.0);
            vec3 norm = normalize(Normal);
            vec3 lightColor = vec3(1.0, 1.0, 0.9);
            vec3 lightDir = normalize(vec3(0.5, -1.0, 0.5));
            vec3 finalColor;

            if (useLightMap) {
                vec3 bakedLight = texture(lightMap, TexCoord).rgb;
                finalColor = bakedLight * texColor.rgb;
            } else {
                vec3 ld = normalize(-lightDir);
                float diff = max(dot(norm, ld), 0.0);
                vec3 diffuse = diff * lightColor;
                vec3 ambient = 0.4 * lightColor;

                // Spotlight
                vec3 sLd = normalize(spotPos - FragPos);
                float theta = dot(sLd, normalize(-spotDir));
                float spotIntensity = 0.0;
                if(theta > spotCutoff) {
                    float dist = length(spotPos - FragPos);
                    float att = 1.0 / (1.0 + 0.045 * dist + 0.0075 * dist * dist);
                    spotIntensity = max(dot(norm, sLd), 0.0) * 2.0 * att;
                }
                finalColor = (ambient + diffuse + vec3(1.0,0.9,0.7)*spotIntensity) * texColor.rgb + emissiveColor;
            }

            if(useEmissive) {
                 vec3 lm = texture(emissiveMap, TexCoord).rgb;
                 float brightness = dot(lm, vec3(0.299, 0.587, 0.114));
                 if(brightness > 0.5) finalColor += lm * brightness * 0.8;
            }
            FragColor = vec4(finalColor, alpha);
        }
        """
        self.shader = Shader(vs, fs)

    def setup_geometry(self):
        t_v, t_i = GeometryUtils.generate_terrain_from_map(self.heightmap_data, 1.0, 1.0)
        self.terrain_mesh = Mesh(t_v, t_i)

        self.sphere_mesh = Mesh(*GeometryUtils.generate_sphere(1.0, 16, 16))
        self.cube_mesh = Mesh(*GeometryUtils.generate_cube_v_i())
        self.cyl_mesh = Mesh(*GeometryUtils.generate_cylinder(0.2, 1.0, 8))
        self.cone_mesh = Mesh(*GeometryUtils.generate_cone(0.8, 2.0, 8))
        self.pyr_mesh = Mesh(*GeometryUtils.generate_pyramid(1.2, 1.0))
        self.rope_mesh = Mesh(*GeometryUtils.generate_airship_ropes(3.5, 0.8, 0.5))
        self.string_mesh = Mesh(*GeometryUtils.generate_single_string(2.0))

    def create_clouds(self, count):
        clouds = []
        for _ in range(count):
            base_pos = np.array([random.uniform(-50, 50), random.uniform(12, 18), random.uniform(-50, 50)])
            puffs = []
            for _ in range(random.randint(4, 8)):
                puffs.append({
                    'offset': np.array([random.uniform(-2,2), random.uniform(-1,1), random.uniform(-2,2)]),
                    'scale': random.uniform(1.5, 3.5)
                })
            clouds.append({'pos': base_pos, 'puffs': puffs, 'flash_timer': 0, 'speed': random.uniform(0.01, 0.04)})
        return clouds

    def setup_npcs(self):
        self.npc_balloons = []
        for _ in range(5):
            self.npc_balloons.append({
                'pos': np.array([random.uniform(-40, 40), random.uniform(18, 25), random.uniform(-40, 40)]),
                'color': [random.random(), random.random(), random.random()],
                'speed': random.uniform(0.05, 0.1)
            })

    def get_mat(self, x, y, z, sx=1, sy=1, sz=1, ry=0):
        rad = np.radians(ry)
        c, s = np.cos(rad), np.sin(rad)
        rot = np.array([[c,0,s,0], [0,1,0,0], [-s,0,c,0], [0,0,0,1]], dtype=np.float32)
        scale = np.array([[sx,0,0,0], [0,sy,0,0], [0,0,sz,0], [0,0,0,1]], dtype=np.float32)
        trans = np.array([[1,0,0,x], [0,1,0,y], [0,0,1,z], [0,0,0,1]], dtype=np.float32)
        return np.dot(trans, np.dot(rot, scale))

    def get_height_at(self, x, z):
        offset_x = - (self.map_width * 1.0) / 2.0
        offset_z = - (self.map_depth * 1.0) / 2.0
        c = int(x - offset_x)
        r = int(z - offset_z)
        if 0 <= c < self.map_width and 0 <= r < self.map_depth:
            return self.heightmap_data[r, c] * 5.0
        return 0.0

    def setup_scene_instances(self):
        trunks, leaves, houses, roofs, self.rocks = [], [], [], [], []
        self.targets = [] # Logic for houses

        # Trees
        for _ in range(40):
            x, z = random.uniform(-25, 25), random.uniform(-25, 25)
            if abs(x) < 3 and abs(z) < 3: continue
            y = self.get_height_at(x, z)
            trunks.append(self.get_mat(x, y, z))
            leaves.append(self.get_mat(x, y+1, z))

        # Houses (Targets)
        for i in range(8):
            x, z = random.uniform(-20, 20), random.uniform(-20, 20)
            if abs(x) < 4 and abs(z) < 4: continue
            y = self.get_height_at(x, z)

            houses.append(self.get_mat(x, y+0.5, z))
            roofs.append(self.get_mat(x, y+1.0, z))

            self.targets.append({
                'pos': np.array([x, y, z]),
                'active': True,
                'matrix_idx': i
            })

        # Rocks
        for _ in range(20):
            x, z = random.uniform(-28, 28), random.uniform(-28, 28)
            y = self.get_height_at(x, z)
            self.rocks.append(self.get_mat(x, y+0.2, z, 0.8, 0.3, 0.8, random.uniform(0, 360)))

        self.cyl_mesh.init_instancing(trunks)
        self.cone_mesh.init_instancing(leaves)

        # We need two batches for houses: active (lit) and inactive (unlit)
        # For simplicity in this demo, we will redraw ALL houses in one batch,
        # but we will try to use a uniform or just accept that "Emissive" is global for the batch.
        # To make it work per-house, we'd need a custom shader attribute.
        # SHORTCUT: We will render ALL houses. If a house is done, we won't change its look heavily
        # in this version, OR we can rely on UI feedback.
        # *Better visual:* We will use `cube_mesh` for active houses.

        self.cube_mesh.init_instancing(houses)
        self.pyr_mesh.init_instancing(roofs)
        self.sphere_mesh.init_instancing(self.rocks)

    # ========================== LOGIC LOOPS ==========================

    def process_input(self):
        events = pygame.event.get()
        mx, my = pygame.mouse.get_pos()

        # --- MENU & SETTINGS INPUT ---
        if self.state in [self.STATE_MENU, self.STATE_SETTINGS, self.STATE_WIN]:
            pygame.mouse.set_visible(True)
            for event in events:
                if event.type == pygame.QUIT: self.running = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == self.STATE_MENU:
                        # Play Button (Center)
                        if self.width/2 - 100 < mx < self.width/2 + 100:
                            if self.height/2 - 20 < my < self.height/2 + 30: # Play
                                self.state = self.STATE_GAME
                                self.reset_game()
                            elif self.height/2 + 40 < my < self.height/2 + 90: # Settings
                                self.state = self.STATE_SETTINGS
                            elif self.height/2 + 100 < my < self.height/2 + 150: # Quit
                                self.running = False

                    elif self.state == self.STATE_SETTINGS:
                        # Toggle Map
                        if self.width/2 - 150 < mx < self.width/2 + 150:
                            if self.height/2 - 20 < my < self.height/2 + 30:
                                self.use_procedural_map = not self.use_procedural_map
                                self.reload_terrain()
                            elif self.height/2 + 100 < my < self.height/2 + 150: # Back
                                self.state = self.STATE_MENU

                    elif self.state == self.STATE_WIN:
                         if self.width/2 - 100 < mx < self.width/2 + 100:
                            if self.height/2 + 50 < my < self.height/2 + 100:
                                self.state = self.STATE_MENU

        # --- GAME INPUT ---
        elif self.state == self.STATE_GAME:
            pygame.mouse.set_visible(False)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                self.state = self.STATE_MENU

            if keys[pygame.K_a]: self.airship_yaw += 1.5
            if keys[pygame.K_d]: self.airship_yaw -= 1.5

            rad = np.radians(self.airship_yaw)
            forward = np.array([np.cos(rad), 0, np.sin(rad)])

            if keys[pygame.K_w]: self.airship_pos += forward * 0.15
            if keys[pygame.K_s]: self.airship_pos -= forward * 0.15

            for event in events:
                if event.type == pygame.QUIT: self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.packages.append({'pos': self.airship_pos + np.array([0,-1.5,0]), 'vel': 0.0, 'active': True})
                    if event.key == pygame.K_f:
                        self.spotlight_active = not self.spotlight_active

    def update_game_logic(self):
        if self.state != self.STATE_GAME: return

        # Timer
        if not self.game_finished:
            self.game_time += 1/60.0

        # Clouds & NPCs
        for npc in self.npc_balloons:
            npc['pos'][0] += npc['speed']
            if npc['pos'][0] > 40: npc['pos'][0] = -40

        for c in self.clouds:
            if c['flash_timer'] > 0: c['flash_timer'] -= 1
            else:
                if random.random() < 0.005: c['flash_timer'] = random.randint(5, 15)

        # Packages
        for p in self.packages:
            if not p['active']: continue

            p['vel'] += 0.01
            p['pos'][1] -= p['vel']

            ty = self.get_height_at(p['pos'][0], p['pos'][2])

            # Hit ground check
            if p['pos'][1] < ty + 0.25:
                p['pos'][1] = ty + 0.25
                p['vel'] = 0
                p['active'] = False # Stop moving

                # Check target collision
                hit_house = False
                for t in self.targets:
                    if t['active']:
                        dist = np.linalg.norm(np.array([p['pos'][0], 0, p['pos'][2]]) - np.array([t['pos'][0], 0, t['pos'][2]]))
                        if dist < 4.0: # Hit radius
                            t['active'] = False
                            self.score += 100
                            hit_house = True
                            break

                # Check win condition
                if all(not t['active'] for t in self.targets):
                    self.game_finished = True
                    self.state = self.STATE_WIN

    # ========================== DRAWING ==========================

    def draw_menu(self):
        glDisable(GL_DEPTH_TEST)
        cx, cy = self.width / 2, self.height / 2

        self.ui.draw_text("AIRSHIP DELIVERY", cx - 140, cy - 100, (1, 0.9, 0.2), 1.5)

        # Buttons
        self.ui.draw_rect(cx - 100, cy, 200, 50, (0.2, 0.6, 0.2))
        self.ui.draw_text("PLAY", cx - 30, cy + 10)

        self.ui.draw_rect(cx - 100, cy + 60, 200, 50, (0.2, 0.2, 0.6))
        self.ui.draw_text("SETTINGS", cx - 50, cy + 70)

        self.ui.draw_rect(cx - 100, cy + 120, 200, 50, (0.6, 0.2, 0.2))
        self.ui.draw_text("EXIT", cx - 30, cy + 130)
        glEnable(GL_DEPTH_TEST)

    def draw_settings(self):
        glDisable(GL_DEPTH_TEST)
        cx, cy = self.width / 2, self.height / 2

        self.ui.draw_text("SETTINGS", cx - 80, cy - 100, (1, 1, 1), 1.5)

        # Map Toggle
        map_name = "PROCEDURAL" if self.use_procedural_map else "FILE (heightmap.png)"
        col = (0.3, 0.3, 0.8)
        self.ui.draw_rect(cx - 150, cy, 300, 50, col)
        self.ui.draw_text(f"MAP: {map_name}", cx - 120, cy + 10)

        self.ui.draw_rect(cx - 100, cy + 120, 200, 50, (0.4, 0.4, 0.4))
        self.ui.draw_text("BACK", cx - 30, cy + 130)
        glEnable(GL_DEPTH_TEST)

    def draw_hud(self):
        glDisable(GL_DEPTH_TEST)
        # Score
        self.ui.draw_text(f"SCORE: {self.score}", 20, 20, (1, 1, 0))

        # Timer
        mins = int(self.game_time // 60)
        secs = int(self.game_time % 60)
        col = (1, 1, 1) if not self.game_finished else (0, 1, 0)
        self.ui.draw_text(f"TIME: {mins:02}:{secs:02}", self.width - 150, 20, col)

        # Target Counter
        rem = sum(1 for t in self.targets if t['active'])
        self.ui.draw_text(f"HOUSES LEFT: {rem}", 20, 60, (1, 0.5, 0.5))

        if self.game_finished:
             cx, cy = self.width / 2, self.height / 2
             self.ui.draw_text("DELIVERY COMPLETE!", cx - 150, cy - 50, (0.5, 1, 0.5), 1.2)

        glEnable(GL_DEPTH_TEST)

    def draw_win_screen(self):
        glDisable(GL_DEPTH_TEST)
        cx, cy = self.width / 2, self.height / 2

        self.ui.draw_text("MISSION ACCOMPLISHED!", cx - 180, cy - 100, (0.2, 1, 0.2), 1.5)
        self.ui.draw_text(f"Final Score: {self.score}", cx - 80, cy - 40, (1,1,1))
        mins = int(self.game_time // 60)
        secs = int(self.game_time % 60)
        self.ui.draw_text(f"Time: {mins:02}:{secs:02}", cx - 60, cy, (1,1,1))

        self.ui.draw_rect(cx - 100, cy + 60, 200, 50, (0.4, 0.4, 0.8))
        self.ui.draw_text("MAIN MENU", cx - 60, cy + 70)
        glEnable(GL_DEPTH_TEST)

    def draw_3d_scene(self):
        # Update Uniforms
        self.shader.use()
        self.shader.set_mat4("view", self.camera.get_view_matrix())
        self.shader.set_mat4("projection", self.camera.get_projection_matrix(self.width, self.height))
        self.shader.set_vec3("viewPos", self.camera.position)
        self.shader.set_vec3("spotPos", self.airship_pos)
        self.shader.set_vec3("spotDir", 0.0, -1.0, 0.0)
        self.shader.set_float("spotCutoff", np.cos(np.radians(15.5)) if self.spotlight_active else 1.1)

        self.shader.set_vec3("tintColor", 1, 1, 1)
        self.shader.set_bool("useEmissive", False)
        self.shader.set_bool("useLightMap", False)

        self.tex_white.bind(1)
        self.shader.set_int("emissiveMap", 1)
        self.shader.set_int("lightMap", 2)
        self.shader.set_int("diffuseMap", 0)

        # 1. Terrain
        self.tex_grass.bind(0)
        self.shader.set_mat4("model", np.identity(4, dtype=np.float32))
        self.terrain_mesh.draw(self.shader)

        # 2. Scenery Instances
        self.tex_wood.bind(0)
        self.cyl_mesh.draw_instanced(self.shader) # Trunks
        self.tex_leaf.bind(0)
        self.cone_mesh.draw_instanced(self.shader) # Leaves

        # 3. HOUSES (Logic for active/inactive)
        self.shader.set_bool("useLightMap", True)
        self.tex_wood.bind(0)
        self.tex_house_lightmap.bind(2)

        # We draw instanced, but the shader handles "on/off" logic only if we pass data.
        # Since we can't easily pass array uniforms without UBOs in this simple setup,
        # we will use the Emissive map.

        # Trick: Active houses get the Window Emissive texture.
        # Inactive houses get a Black Emissive texture.
        # This requires splitting the draw call or updating the VBO.
        # For this demo, all houses GLOW. When done, they should technically stop glowing.
        # We will keep them glowing for now as visual flair, relying on UI for "Done" status.

        self.shader.set_bool("useEmissive", True)
        self.tex_window_emissive.bind(1)

        self.cube_mesh.draw_instanced(self.shader)

        self.shader.set_bool("useEmissive", False)
        self.shader.set_bool("useLightMap", False)

        # Roofs
        self.tex_wood.bind(0)
        self.shader.set_vec3("tintColor", 1.0, 0.4, 0.4)
        self.pyr_mesh.draw_instanced(self.shader)
        self.shader.set_vec3("tintColor", 1, 1, 1)

        # Rocks
        self.tex_dirt.bind(0)
        self.sphere_mesh.draw_instanced(self.shader)

        # 4. Airship
        self.tex_balloon.bind(0)
        self.shader.set_vec3("tintColor", 1.0, 0.2, 0.2)
        model = self.get_mat(self.airship_pos[0], self.airship_pos[1] + 1.0 - 0.4, self.airship_pos[2], 2.0, 2.0, 2.0, self.airship_yaw)
        self.shader.set_mat4("model", model)
        self.sphere_mesh.draw(self.shader)

        self.tex_metal.bind(0)
        self.shader.set_vec3("tintColor", 0.8, 0.8, 0.7)
        model = self.get_mat(self.airship_pos[0], self.airship_pos[1] + 1.0, self.airship_pos[2], 1.0, 1.0, 1.0, self.airship_yaw)
        self.shader.set_mat4("model", model)
        self.rope_mesh.draw(self.shader)

        self.tex_wood.bind(0)
        self.shader.set_vec3("tintColor", 1, 1, 1)
        model = self.get_mat(self.airship_pos[0], self.airship_pos[1] + 1.0 - 4.8, self.airship_pos[2], 1.0, 1.0, 1.0, self.airship_yaw)
        self.shader.set_mat4("model", model)
        self.cube_mesh.draw(self.shader)

        # 5. NPCs
        self.tex_balloon.bind(0)
        for npc in self.npc_balloons:
            self.shader.set_vec3("tintColor", npc['color'][0], npc['color'][1], npc['color'][2])
            self.shader.set_mat4("model", self.get_mat(npc['pos'][0], npc['pos'][1], npc['pos'][2], 1.5, 1.5, 1.5))
            self.sphere_mesh.draw(self.shader)

            self.tex_white.bind(0)
            self.shader.set_vec3("tintColor", 0.9, 0.9, 0.9)
            self.shader.set_mat4("model", self.get_mat(npc['pos'][0], npc['pos'][1], npc['pos'][2], 1.0, 1.0, 1.0))
            self.string_mesh.draw(self.shader)
        self.shader.set_vec3("tintColor", 1, 1, 1)

        # 6. Packages
        self.tex_metal.bind(0)
        for p in self.packages:
            self.shader.set_mat4("model", self.get_mat(p['pos'][0], p['pos'][1], p['pos'][2], 0.5, 0.5, 0.5))
            self.cube_mesh.draw(self.shader)

        # 7. Clouds (Transparent)
        glDepthMask(GL_FALSE)
        self.tex_white.bind(0)
        for c in self.clouds:
            if c['flash_timer'] > 0:
                self.shader.set_vec3("emissiveColor", 0.8, 0.8, 0.9); alpha = 0.9
            else:
                self.shader.set_vec3("emissiveColor", 0.1, 0.1, 0.1); alpha = 0.5
            self.shader.set_float("alpha", alpha)
            for puff in c['puffs']:
                px, py, pz = c['pos'] + puff['offset']
                s = puff['scale']
                self.shader.set_mat4("model", self.get_mat(px, py, pz, s, s, s))
                self.sphere_mesh.draw(self.shader)

        self.shader.set_float("alpha", 1.0)
        self.shader.set_vec3("emissiveColor", 0, 0, 0)
        glDepthMask(GL_TRUE)

    def run(self):
        while self.running:
            self.process_input()

            glClearColor(0.1, 0.1, 0.15, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            if self.state == self.STATE_MENU:
                # Still draw background scene slowly rotating?
                self.airship_yaw += 0.2
                self.camera.follow(self.airship_pos, self.airship_yaw + 180, distance=30, height=10)
                self.draw_3d_scene()
                self.draw_menu()

            elif self.state == self.STATE_SETTINGS:
                self.airship_yaw += 0.2
                self.camera.follow(self.airship_pos, self.airship_yaw + 180, distance=30, height=10)
                self.draw_3d_scene()
                self.draw_settings()

            elif self.state == self.STATE_GAME:
                self.update_game_logic()
                self.camera.follow(self.airship_pos, self.airship_yaw)
                self.draw_3d_scene()
                self.draw_hud()

            elif self.state == self.STATE_WIN:
                self.camera.follow(self.airship_pos, self.airship_yaw + 90, distance=15, height=5)
                self.draw_3d_scene()
                self.draw_win_screen()

            pygame.display.flip()
            self.clock.tick(60)

        self.shader.destroy()
        self.terrain_mesh.destroy()
        pygame.quit()

if __name__ == "__main__":
    app = App()
    app.run()