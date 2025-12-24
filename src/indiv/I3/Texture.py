import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import ctypes
import math
import random

# ==============================================================================
# 1. TEXTURE & HEIGHTMAP UTILS
# ==============================================================================
class TextureUtils:
    @staticmethod
    def generate_checkerboard(width, height, color1=(255, 255, 255), color2=(0, 0, 0)):
        """Generates a checkerboard pattern."""
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
        """Generates a simple noise texture (preventing overflow)."""
        # Use int16 to allow math operations without wrapping
        arr = np.random.randint(0, 40, (height, width, 3), dtype=np.int16)
        base = np.array(color_base, dtype=np.int16)
        # Add and clip to valid 0-255 range
        return np.clip(base + arr, 0, 255).astype(np.uint8)

    @staticmethod
    def load_heightmap_from_image(filepath, width, depth):
        """Загружает heightmap из файла изображения."""
        try:
            print(f"Loading heightmap from {filepath}...")
            # 1. Загружаем изображение
            surf = pygame.image.load(filepath)

            # 2. Масштабируем изображение под размеры сетки террейна
            # Это важно, чтобы количество вершин совпадало с логикой генерации
            surf = pygame.transform.scale(surf, (width, depth))

            # 3. Получаем массив пикселей (Width, Height, 3)
            # pygame.surfarray.array3d возвращает оси [x, y, rgb]
            rgb_array = pygame.surfarray.array3d(surf)

            # 4. Преобразуем в градации серого и нормализуем
            # Берем среднее арифметическое (R+G+B)/3
            # Транспонируем (.T), так как array3d дает [col, row], а нам нужно [row, col]
            grayscale = np.mean(rgb_array, axis=2).T

            # 5. Нормализуем в диапазон 0.0 - 1.0, затем умножаем на силу высоты
            # (делим на 255, так как цвета 0-255)
            # Умножаем на 2.0 или 3.0, чтобы горы были повыше
            height_data = (grayscale / 255.0) * 2.0

            return height_data.astype(np.float32)

        except Exception as e:
            print(f"Error loading heightmap: {e}")
            print("Falling back to procedural generation.")
            return TextureUtils.generate_heightmap(width, depth)

    @staticmethod
    def generate_heightmap(width, depth):
        """Generates terrain data."""
        # 1. Random Noise
        data = np.random.rand(depth, width) * 2.0
        # 2. Smoothing (Box Blur) to look like rolling hills
        for _ in range(16):
            data[1:-1, 1:-1] = (
                data[:-2, 1:-1] + data[2:, 1:-1] +
                data[1:-1, :-2] + data[1:-1, 2:] +
                data[1:-1, 1:-1] * 4
            ) / 8.0
        return data

    @staticmethod
    def create_house_lightmap():
        """Драматичный lightmap с сильными тенями"""
        size = 128
        lightmap = np.ones((size, size, 3), dtype=np.float32)

        # Холодный цвет тени, тёплый цвет света
        shadow_color = np.array([0.4, 0.5, 0.7], dtype=np.float32)  # Голубоватая тень
        light_color = np.array([1.0, 0.95, 0.85], dtype=np.float32)  # Тёплый свет

        for y in range(size):
            progress = y / size

            # Экспоненциальный градиент (резкий переход)
            shadow_strength = np.power(progress, 2.0)  # 0→1, но нелинейно

            for x in range(size):
                # Смешиваем холодную тень и тёплый свет
                color = light_color * (1 - shadow_strength) + shadow_color * shadow_strength

                # AO в углах
                edge_dist = min(x, size - x, y, size - y) / (size / 2)
                ao = 0.5 + 0.5 * min(1.0, edge_dist * 2.0)

                lightmap[y, x] = color * ao

        # Сглаживание
        for _ in range(3):
            temp = lightmap.copy()
            for y in range(1, size - 1):
                for x in range(1, size - 1):
                    lightmap[y, x] = temp[y-1:y+2, x-1:x+2].mean(axis=(0, 1))

        lightmap = np.clip(lightmap, 0.0, 1.0)
        lightmap_uint8 = (lightmap * 255).astype(np.uint8)

        # DEBUG: Сохраняем для просмотра
        # import cv2
        # cv2.imwrite("house_lightmap_debug.png", cv2.cvtColor(lightmap_uint8, cv2.COLOR_RGB2BGR))
        # print("Lightmap saved to house_lightmap_debug.png")

        return lightmap_uint8

class Texture:
    def __init__(self, filepath=None, texture_type='diffuse', gen_color=None, custom_array=None):
        self.texture_id = glGenTextures(1)
        self.type = texture_type

        data = None
        width, height = 64, 64

        # 1. Try Loading File
        loaded = False
        if filepath:
            try:
                surf = pygame.image.load(filepath)
                surf = pygame.transform.flip(surf, False, True) # OpenGL flips Y
                data = pygame.image.tostring(surf, "RGB", 1)
                width, height = surf.get_width(), surf.get_height()
                loaded = True
            except:
                print(f"Texture not found: {filepath}. Generating fallback.")

        # 2. Fallback Generation
        if not loaded:
            if custom_array is not None:
                array_data = custom_array
            elif gen_color:
                array_data = TextureUtils.generate_noise_texture(64, 64, gen_color)
            else:
                array_data = TextureUtils.generate_checkerboard(64, 64)

            width, height = array_data.shape[1], array_data.shape[0]
            data = array_data.tobytes()

        # 3. Upload to GPU
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, data)
        glGenerateMipmap(GL_TEXTURE_2D)

        # Parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)

    def bind(self, unit=0):
        glActiveTexture(GL_TEXTURE0 + unit)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)