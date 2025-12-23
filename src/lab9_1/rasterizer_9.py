import pygame
import numpy as np


def interpolate(y, y0, y1, x0, x1):
    """Линейная интерполяция значения x для строки y"""
    if y1 == y0: return x0
    return x0 + (x1 - x0) * (y - y0) / (y1 - y0)


def interpolate_attr(y, y0, y1, a0, a1):
    """Интерполяция атрибута (цвета или нормали)"""
    if y1 == y0: return a0
    # Для numpy массивов это работает поэлементно
    return a0 + (a1 - a0) * (y - y0) / (y1 - y0)


def draw_scanline_gouraud(pixels, y, x_start, x_end, c_start, c_end):
    """Рисует горизонтальную линию с интерполяцией цвета (Гуро)"""
    x_s, x_e = int(x_start), int(x_end)
    if x_s >= x_e: return

    # Оптимизация: используем numpy для создания градиента строки сразу
    steps = x_e - x_s

    # Генерируем массив цветов для строки
    # color = start + (end-start) * ratio
    ratios = np.linspace(0, 1, steps)

    # c_start и c_end должны быть numpy array (3,)
    # Делаем broadcasting: (3,) + (3,) * (N,) -> (N, 3)
    # Нужно изменить размерности для broadcasting

    diff = c_end - c_start
    # R channel
    rs = c_start[0] + diff[0] * ratios
    gs = c_start[1] + diff[1] * ratios
    bs = c_start[2] + diff[2] * ratios

    # Собираем в целые числа для цвета
    rs = np.clip(rs, 0, 255).astype(int)
    gs = np.clip(gs, 0, 255).astype(int)
    bs = np.clip(bs, 0, 255).astype(int)

    # Формируем цвета для pixelarray (формат int: (r<<16) + (g<<8) + b)
    # Pygame PixelArray принимает целые числа
    colors = (rs << 16) | (gs << 8) | bs

    try:
        # Пишем всю строку сразу
        pixels[x_s:x_e, y] = colors
    except IndexError:
        pass


def rasterize_gouraud(surface, v1, v2, v3, c1, c2, c3):
    """
    v1, v2, v3: кортежи (x, y) экранных координат
    c1, c2, c3: цвета вершин (np.array rgb 0-255)
    """
    # Сортировка вершин по Y
    verts = [(v1, c1), (v2, c2), (v3, c3)]
    verts.sort(key=lambda v: v[0][1])

    (x1, y1), col1 = verts[0]
    (x2, y2), col2 = verts[1]
    (x3, y3), col3 = verts[2]

    y1, y2, y3 = int(y1), int(y2), int(y3)
    if y1 == y3: return  # Вырожденный треугольник

    pixels = pygame.PixelArray(surface)

    # Разделяем треугольник на две части: верхнюю (flat bottom) и нижнюю (flat top)
    # P4 - точка на длинной стороне (v1-v3), лежащая на высоте y2

    # Обходим строки
    for y in range(y1, y3 + 1):
        if y < 0 or y >= surface.get_height(): continue

        # Интерполяция для длинной стороны (1-3)
        xa = interpolate(y, y1, y3, x1, x3)
        ca = interpolate_attr(y, y1, y3, col1, col3)

        # Интерполяция для коротких сторон
        if y < y2:
            xb = interpolate(y, y1, y2, x1, x2)
            cb = interpolate_attr(y, y1, y2, col1, col2)
        else:
            xb = interpolate(y, y2, y3, x2, x3)
            cb = interpolate_attr(y, y2, y3, col2, col3)

        if xa > xb:
            xa, xb = xb, xa
            ca, cb = cb, ca

        draw_scanline_gouraud(pixels, y, xa, xb, ca, cb)

    pixels.close()


# --- TOON SHADING ---

def calculate_toon_color(normal, light_dir, base_color):
    """Расчет цвета пикселя по модели Toon Shading"""
    # Нормализуем интерполированную нормаль
    len_n = np.linalg.norm(normal)
    if len_n == 0: return np.array([0, 0, 0])
    n = normal / len_n

    # Скалярное произведение (Lambert)
    intensity = np.dot(n, light_dir)
    intensity = max(0, intensity)

    # Квантование (Toon ramp)
    if intensity > 0.95:
        factor = 1.0
    elif intensity > 0.5:
        factor = 0.7
    elif intensity > 0.25:
        factor = 0.4
    else:
        factor = 0.2

    final = base_color * factor
    return np.clip(final, 0, 255).astype(int)


def draw_scanline_phong(pixels, y, x_start, x_end, n_start, n_end, light_dir, obj_color):
    """Рисует строку с интерполяцией нормали и расчетом Toon Shading"""
    x_s, x_e = int(x_start), int(x_end)
    steps = x_e - x_s
    if steps <= 0: return

    # Интерполяция нормалей (линейная)
    ratios = np.linspace(0, 1, steps)
    diff = n_end - n_start

    # Векторизованный расчет нормалей для всей строки
    # (Steps, 3)
    nx = n_start[0] + diff[0] * ratios
    ny = n_start[1] + diff[1] * ratios
    nz = n_start[2] + diff[2] * ratios

    # Объединяем в (Steps, 3)
    normals = np.stack((nx, ny, nz), axis=1)

    # Нормализация (медленная часть в Python, но numpy спасает)
    norms = np.linalg.norm(normals, axis=1, keepdims=True)
    norms[norms == 0] = 1
    normals /= norms

    # Dot product с направлением света
    # Light dir (3,) dot Normals (Steps, 3) -> (Steps,)
    intensity = np.dot(normals, light_dir)

    # Квантование (Toon) векторизованно
    factors = np.select(
        [intensity > 0.95, intensity > 0.5, intensity > 0.25],
        [1.0, 0.7, 0.4],
        default=0.2
    )

    # Применяем цвет
    # obj_color (3,) * factors (Steps, 1)
    r = (obj_color[0] * factors).astype(int)
    g = (obj_color[1] * factors).astype(int)
    b = (obj_color[2] * factors).astype(int)

    # Собираем цвета для Pygame
    colors = (np.clip(r, 0, 255) << 16) | (np.clip(g, 0, 255) << 8) | np.clip(b, 0, 255)

    try:
        pixels[x_s:x_e, y] = colors
    except IndexError:
        pass


def rasterize_phong_toon(surface, v1, v2, v3, n1, n2, n3, light_dir, color):
    """
    n1, n2, n3: нормали вершин (World Space)
    light_dir: вектор света (направление на свет)
    color: базовый цвет объекта (Diffuse)
    """
    verts = [(v1, n1), (v2, n2), (v3, n3)]
    verts.sort(key=lambda v: v[0][1])

    (x1, y1), norm1 = verts[0]
    (x2, y2), norm2 = verts[1]
    (x3, y3), norm3 = verts[2]

    y1, y2, y3 = int(y1), int(y2), int(y3)
    if y1 == y3: return

    pixels = pygame.PixelArray(surface)

    for y in range(y1, y3 + 1):
        if y < 0 or y >= surface.get_height(): continue

        xa = interpolate(y, y1, y3, x1, x3)
        na = interpolate_attr(y, y1, y3, norm1, norm3)

        if y < y2:
            xb = interpolate(y, y1, y2, x1, x2)
            nb = interpolate_attr(y, y1, y2, norm1, norm2)
        else:
            xb = interpolate(y, y2, y3, x2, x3)
            nb = interpolate_attr(y, y2, y3, norm2, norm3)

        if xa > xb:
            xa, xb = xb, xa
            na, nb = nb, na

        draw_scanline_phong(pixels, y, xa, xb, na, nb, light_dir, color)

    pixels.close()