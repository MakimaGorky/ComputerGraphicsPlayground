import pygame
import math
import numpy as np
from typing import List, Tuple, Optional
import config

PIVOT = (300, 300)  # hold my 🍺
Z_PIVOT = -300  # hold my 🍺
WIDTH = 0
HEIGHT = 0


# ===== UI =====

class Vector2:
    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = x
        self.y = y


class Color:
    def __init__(self, r: int = 0, g: int = 0, b: int = 0, a: int = 255):
        self.r = r
        self.g = g
        self.b = b
        self.a = a


class Rectangle:
    def __init__(self, x: float = 0.0, y: float = 0.0, width: float = 0.0, height: float = 0.0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height


class WindowInfo:
    def __init__(self):
        self.width = 0
        self.height = 0
        self.center = Vector2()


def get_window_info(screen) -> WindowInfo:
    result = WindowInfo()
    info = pygame.display.Info()
    result.width = info.current_w
    result.height = info.current_h
    result.center.x = result.width / 2.0
    result.center.y = result.height / 2.0
    return result


def button(screen, font, rect: Rectangle, text: str) -> bool:
    mouse_pos = pygame.mouse.get_pos()

    is_hovered = (rect.x <= mouse_pos[0] <= rect.x + rect.width and
                  rect.y <= mouse_pos[1] <= rect.y + rect.height)

    color = (100, 100, 200) if is_hovered else (70, 70, 170)

    pygame.draw.rect(screen, color, (rect.x, rect.y, rect.width, rect.height))
    pygame.draw.rect(screen, (255, 255, 255), (rect.x, rect.y, rect.width, rect.height), 2)

    text_surface = font.render(text, True, (255, 255, 255))
    text_x = rect.x + (rect.width - text_surface.get_width()) / 2
    text_y = rect.y + (rect.height - text_surface.get_height()) / 2
    screen.blit(text_surface, (text_x, text_y))

    return is_hovered and pygame.mouse.get_pressed()[0]


def input_box(screen, font, rect: Rectangle, text: str, active: bool) -> str:
    mouse_pos = pygame.mouse.get_pos()
    is_hovered = (rect.x <= mouse_pos[0] <= rect.x + rect.width and
                  rect.y <= mouse_pos[1] <= rect.y + rect.height)

    color = (240, 240, 240) if active else (220, 220, 220)
    if is_hovered:
        color = (250, 250, 250)

    pygame.draw.rect(screen, color, (rect.x, rect.y, rect.width, rect.height))
    pygame.draw.rect(screen, (0, 0, 0), (rect.x, rect.y, rect.width, rect.height), 2)

    text_surface = font.render(text, True, (0, 0, 0))
    text_x = rect.x + 5
    text_y = rect.y + (rect.height - text_surface.get_height()) / 2
    screen.blit(text_surface, (text_x, text_y))

    return is_hovered and pygame.mouse.get_pressed()[0]


# ===== 3D Graphics =====

class Point:
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z

    def to_homogeneous(self):
        return np.array([self.x, self.y, self.z, 1.0])

    def from_homogeneous(self, h):
        self.x = h[0]
        self.y = h[1]
        self.z = h[2]

    def __str__(self):
        return f"({self.x:.1f}, {self.y:.1f}, {self.z:.1f})"


class Polygon:
    def __init__(self, points: List[Point] = []):
        self.vertices = points.copy()

    def add_vertex(self, p: Point):
        self.vertices.append(p)

    def get_center(self) -> Point:
        if not self.vertices:
            return Point(0, 0, 0)
        cx = sum(v.x for v in self.vertices) / len(self.vertices)
        cy = sum(v.y for v in self.vertices) / len(self.vertices)
        cz = sum(v.z for v in self.vertices) / len(self.vertices)
        return Point(cx, cy, cz)

    def apply_transformation(self, matrix: np.ndarray):
        for vertex in self.vertices:
            h = vertex.to_homogeneous()
            transformed = np.dot(matrix, h)
            vertex.from_homogeneous(transformed)

    def __len__(self):
        return len(self.vertices)

    def __iter__(self):
        return iter(self.vertices)

    def __getitem__(self, index):
        return self.vertices[index]


class Object:
    def __init__(self, polies: List[Polygon] = []):
        self.polygons = polies.copy()

    def add_face(self, p: Polygon):
        self.polygons.append(p)

    def get_center(self) -> Point:
        all_vertices = []
        for poly in self.polygons:
            all_vertices.extend(poly.vertices)

        if not all_vertices:
            return Point(0, 0, 0)

        cx = sum(v.x for v in all_vertices) / len(all_vertices)
        cy = sum(v.y for v in all_vertices) / len(all_vertices)
        cz = sum(v.z for v in all_vertices) / len(all_vertices)
        return Point(cx, cy, cz)

    def apply_transformation(self, matrix: np.ndarray):
        for poly in self.polygons:
            poly.apply_transformation(matrix)

    def __len__(self):
        return len(self.polygons)

    def __iter__(self):
        return iter(self.polygons)

    def __getitem__(self, index):
        return self.polygons[index]


class PolygonProjection:
    def __init__(self, points: List[Tuple[float, float]] = []):
        self.vertices = points.copy()
        self.color = config.BLUE

    def add_vertex(self, point: Tuple[float, float]):
        self.vertices.append(point)

    def draw(self, screen):
        if len(self.vertices) == 1:
            pygame.draw.circle(screen, self.color,
                               (int(self.vertices[0][0] + PIVOT[0]), int(self.vertices[0][1] + PIVOT[1])),
                               config.POINT_RADIUS)
        elif len(self.vertices) == 2:
            pygame.draw.line(screen, self.color,
                             (int(self.vertices[0][0] + PIVOT[0]), int(self.vertices[0][1] + PIVOT[1])),
                             (int(self.vertices[1][0] + PIVOT[0]), int(self.vertices[1][1] + PIVOT[1])),
                             config.LINE_WIDTH)
        else:
            int_vertices = [(int(v[0] + PIVOT[0]), int(v[1] + PIVOT[1])) for v in self.vertices]
            pygame.draw.polygon(screen, self.color, int_vertices, config.LINE_WIDTH)
            for v in int_vertices:
                pygame.draw.circle(screen, config.RED, v, config.VERTEX_RADIUS)


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


# ===== Рендеринг =====

def render_point(vertex: Point, method: str, window: WindowInfo):
    vertex_h = np.array([vertex.x, vertex.y, vertex.z + Z_PIVOT, 1])

    if method == "Аксонометрическая":
        a = np.radians(config.ANGLE)
        projection_matrix = np.array([
            [1, 0, 0.5 * np.cos(a), 0],
            [0, 1, 0.5 * np.cos(a), 0],
            [0, 0, 0, 0],
            [0, 0, 0, 1]
        ])
    else:  # Перспективная
        c = config.V_POINT
        projection_matrix = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 0],
            [0, 0, -1 / c,  1]
        ])

    projected_vertex = np.dot(projection_matrix, vertex_h)

    if projected_vertex[3] != 0:
        x_normalized = projected_vertex[0] / projected_vertex[3]
        y_normalized = projected_vertex[1] / projected_vertex[3]
        return (x_normalized, y_normalized)

    return (0, 0)


def render_polygon(poly: Polygon, method: str, window: WindowInfo):
    pp = PolygonProjection()
    for v in poly.vertices:
        p = render_point(v, method, window)
        pp.add_vertex(p)
    return pp


def render_object(obj: Object, method: str, window: WindowInfo):
    projected_obj = []
    for p in obj.polygons:
        projected_obj.append(render_polygon(p, method, window))
    return projected_obj


# ===== Создание объектов =====

def create_cube() -> Object:
    points = [
        Point(0.0, 0.0, 0.0),
        Point(200.0, 0.0, 0.0),
        Point(200.0, 200.0, 0.0),
        Point(0.0, 200.0, 0.0),
        Point(0.0, 0.0, 200.0),
        Point(200.0, 0.0, 200.0),
        Point(200.0, 200.0, 200.0),
        Point(0.0, 200.0, 200.0)
    ]

    cube = Object([
        Polygon([points[0], points[1], points[2], points[3]]),
        Polygon([points[0], points[1], points[5], points[4]]),
        Polygon([points[1], points[2], points[6], points[5]]),
        Polygon([points[2], points[3], points[7], points[6]]),
        Polygon([points[0], points[3], points[7], points[4]]),
        Polygon([points[4], points[5], points[6], points[7]])
    ])
    return cube


def create_tetrahedron() -> Object:
    cube = create_cube()
    tetr = Object()

    vert = [
        cube.polygons[0].vertices[1],
        cube.polygons[0].vertices[3],
        cube.polygons[5].vertices[0],
        cube.polygons[5].vertices[2]
    ]

    tetr.add_face(Polygon([vert[1], vert[2], vert[3]]))
    tetr.add_face(Polygon([vert[0], vert[1], vert[2]]))
    tetr.add_face(Polygon([vert[0], vert[2], vert[3]]))
    tetr.add_face(Polygon([vert[0], vert[3], vert[1]]))

    return tetr


def create_octahedron() -> Object:
    cube = create_cube()
    vert = []
    for f in cube.polygons:
        vert.append(f.get_center())

    octa = Object()
    octa.add_face(Polygon([vert[0], vert[1], vert[4]]))
    octa.add_face(Polygon([vert[5], vert[1], vert[4]]))

    for i in range(3):
        octa.add_face(Polygon([vert[0], vert[i + 1], vert[(i + 1) % 4 + 1]]))
        octa.add_face(Polygon([vert[5], vert[i + 1], vert[(i + 1) % 4 + 1]]))

    return octa


def create_icosahedron() -> Object:
    # Золотое сечение
    phi = (1 + 5**0.5) / 2
    a = 100

    # Вершины икосаэдра
    vertices = [
        Point(-a, phi * a, 0), Point(a, phi * a, 0), Point(-a, -phi * a, 0), Point(a, -phi * a, 0),
        Point(0, -a, phi * a), Point(0, a, phi * a), Point(0, -a, -phi * a), Point(0, a, -phi * a),
        Point(phi * a, 0, -a), Point(phi * a, 0, a), Point(-phi * a, 0, -a), Point(-phi * a, 0, a)
    ]

    # 12 вершин икосаэдра
    # for i in [-1, 1]:
    #     for j in [-1, 1]:
    #         vertices.append(Point(0, i * phi * a, j * a))
    #         vertices.append(Point(i * phi * a, j * a, 0))
    #         vertices.append(Point(i * a, 0, j * phi * a))

    icosa = Object()

    # Создаем 20 треугольных граней икосаэдра
    faces_indices = [
        [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
        [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
        [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
    ]

    for face in faces_indices:
        icosa.add_face(Polygon([vertices[face[0]], vertices[face[1]], vertices[face[2]]]))

    # icosa.apply_transformation(scale_matrix(a, a, a))

    return icosa

def create_dodecahedron() -> Object:
    # Создаем додекаэдр как двойственный икосаэдру
    # icosa = create_icosahedron()
    phi = (1 + np.sqrt(5)) / 2;
    a = 100

    vert = [
        Point(a, a, a), Point(a,a,-a), Point(a,-a,a), Point(a,-a,-a),
        Point(-a, a, a), Point(-a,a,-a), Point(-a,-a,a), Point(-a,-a,-a),
        Point(0, 1 / phi * a, phi * a), Point(0, 1 / phi * a, -phi * a), Point(0, -1/phi * a, phi * a), Point(0, -1/phi * a, -phi * a),
        Point(1 / phi * a, phi * a, 0), Point(1 / phi * a, -phi * a, 0), Point(-1/phi * a, phi * a, 0), Point(-1/phi * a, -phi * a, 0),
        Point(phi * a, 0, 1 / phi * a), Point(phi * a, 0, -1 / phi * a), Point(-phi * a, 0, 1/phi * a), Point(-phi * a, 0, -1/phi * a),
    ]
    # for f in icosa.polygons:
    #     vert.append(f.get_center())

    dodeca = Object()

    # Додекаэдр имеет 12 пятиугольных граней
    # Группируем вершины по 5 вокруг каждой исходной вершины икосаэдра
    face_groups = [
        [0, 8, 10, 2, 16],    # Верхняя грань
        [0, 16, 17, 1, 12],    # Нижняя грань
        [0, 12, 14, 4, 8],  # Боковые грани
        [17, 3, 11, 9, 1],
        [2, 10, 6, 15, 13],
        [13, 15, 7, 11, 3],
        [17, 16, 2, 13, 3],
        [14, 5, 19, 18, 4],
        [9, 11, 7, 19, 5],
        [18, 19, 7, 15, 6],
        [12, 1, 9, 5, 14],
        [4, 18, 6, 10, 8]
    ]

    for group in face_groups:
        face_vertices = [vert[i] for i in group]
        dodeca.add_face(Polygon(face_vertices))

    return dodeca


# ===== Main =====

class ObjectOption:
    def __init__(self, name: str, creator):
        self.name = name
        self.create = creator


def task():
    pygame.init()

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("3DRenderer")

    window_info = get_window_info(screen)

    objects = [
        ObjectOption("Тетраэдр", create_tetrahedron),
        ObjectOption("Гексаэдр", create_cube),
        ObjectOption("Октаэдр", create_octahedron),
        ObjectOption("Икосаэдр", create_icosahedron),
        ObjectOption("Додекаэдр", create_dodecahedron)
    ]

    object_count = len(objects)
    current_object = 0
    show_dropdown_objects = False
    ui_background_color = (220, 220, 220)

    font = pygame.font.Font(None, 28)
    small_font = pygame.font.Font(None, 24)

    dropdown_bounds_objects = Rectangle(20, 20, 180, 35)

    renders = ["Аксонометрическая", "Перспективная"]
    renders_count = len(renders)
    current_render = 0
    show_dropdown_renders = False
    dropdown_bounds_renders = Rectangle(220, 20, 230, 35)

    main_object: Optional[Object] = objects[current_object].create()
    rendered_object = render_object(main_object, renders[current_render], window_info)

    last_object = -1
    last_render = -1

    # Поля ввода параметров
    input_boxes = {
        "translation_x": "20",
        "translation_y": "0",
        "translation_z": "0",
        "scale_x": "1.1",
        "scale_y": "1.1",
        "scale_z": "1.1",
        "rotation_angle": "15",
        "custom_line_p1": "0,0,0",
        "custom_line_p2": "100,100,100",
        "custom_rotation_angle": "30"
    }

    active_input = None

    # Кнопки управления
    y_offset = 80
    btn_width, btn_height = 200, 35

    transform_buttons = [
        Rectangle(1200, y_offset, btn_width, btn_height),  # Перенос
        Rectangle(1200, y_offset + 45, btn_width, btn_height),  # Масштаб
        Rectangle(1200, y_offset + 90, btn_width, btn_height),  # Поворот X
        Rectangle(1200, y_offset + 135, btn_width, btn_height),  # Поворот Y
        Rectangle(1200, y_offset + 180, btn_width, btn_height),  # Поворот Z
        Rectangle(1200, y_offset + 225, btn_width, btn_height),  # Отражение XY
        Rectangle(1200, y_offset + 270, btn_width, btn_height),  # Отражение XZ
        Rectangle(1200, y_offset + 315, btn_width, btn_height),  # Отражение YZ
        Rectangle(1200, y_offset + 360, btn_width, btn_height),  # Поворот вокруг произвольной прямой
        Rectangle(1200, y_offset + 405, btn_width, btn_height),  # Сброс
    ]

    # Поля ввода
    input_rects = {
        "translation_x": Rectangle(800, y_offset, 80, 30),
        "translation_y": Rectangle(920, y_offset, 80, 30),
        "translation_z": Rectangle(1040, y_offset, 80, 30),
        "scale_x": Rectangle(800, y_offset + 45, 80, 30),
        "scale_y": Rectangle(920, y_offset + 45, 80, 30),
        "scale_z": Rectangle(1040, y_offset + 45, 80, 30),
        "rotation_angle": Rectangle(800, y_offset + 135, 170, 30),
        "custom_line_p1": Rectangle(800, y_offset + 360, 170, 30),
        "custom_line_p2": Rectangle(800, y_offset + 395, 170, 30),
        "custom_rotation_angle": Rectangle(800, y_offset + 430, 170, 30)
    }

    running = True
    clock = pygame.time.Clock()
    button_clicked = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif active_input and event.key == pygame.K_RETURN:
                    active_input = None
                elif active_input:
                    if event.key == pygame.K_BACKSPACE:
                        input_boxes[active_input] = input_boxes[active_input][:-1]
                    else:
                        # Проверяем, что вводим только цифры, запятые, точки и минусы
                        if event.unicode in '0123456789,.-':
                            input_boxes[active_input] += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    button_clicked = True
                    # Проверяем клик по полям ввода
                    active_input = None
                    for key, rect in input_rects.items():
                        if (rect.x <= event.pos[0] <= rect.x + rect.width and
                            rect.y <= event.pos[1] <= rect.y + rect.height):
                            active_input = key
                            break

        screen.fill(ui_background_color)

        if rendered_object:
            for rp in rendered_object:
                rp.draw(screen)

        # Выпадающий список объектов
        if button(screen, font, dropdown_bounds_objects, objects[current_object].name) and button_clicked:
            show_dropdown_objects = not show_dropdown_objects
            button_clicked = False

        if show_dropdown_objects:
            button_cnt = 1
            for i in range(object_count):
                if i == current_object:
                    continue
                option_rect = Rectangle(
                    dropdown_bounds_objects.x,
                    dropdown_bounds_objects.y + button_cnt * 45,
                    dropdown_bounds_objects.width,
                    dropdown_bounds_objects.height
                )
                if button(screen, font, option_rect, objects[i].name) and button_clicked:
                    current_object = i
                    show_dropdown_objects = False
                    button_clicked = False
                button_cnt += 1

        if current_object != last_object:
            main_object = objects[current_object].create()
            rendered_object = render_object(main_object, renders[current_render], window_info)
            last_object = current_object

        # Выпадающий список типов рендера
        if button(screen, font, dropdown_bounds_renders, renders[current_render]) and button_clicked:
            show_dropdown_renders = not show_dropdown_renders
            button_clicked = False

        if show_dropdown_renders:
            button_cnt = 1
            for i in range(renders_count):
                if i == current_render:
                    continue
                option_rect = Rectangle(
                    dropdown_bounds_renders.x,
                    dropdown_bounds_renders.y + button_cnt * 45,
                    dropdown_bounds_renders.width,
                    dropdown_bounds_renders.height
                )
                if button(screen, font, option_rect, renders[i]) and button_clicked:
                    current_render = i
                    show_dropdown_renders = False
                    button_clicked = False
                button_cnt += 1

        if current_render != last_render:
            rendered_object = render_object(main_object, renders[current_render], window_info)
            last_render = current_render

        # Отображение центра объекта
        center = main_object.get_center()
        center_text = small_font.render(f"Центр: {center}", True, (0, 0, 0))
        screen.blit(center_text, (20, 70))

        # Поля ввода и кнопки преобразований

        # Подписи к полям ввода
        screen.blit(small_font.render("dx:", True, (0, 0, 0)), (770, y_offset + 5))
        screen.blit(small_font.render("dy:", True, (0, 0, 0)), (890, y_offset + 5))
        screen.blit(small_font.render("dz:", True, (0, 0, 0)), (1010, y_offset + 5))
        screen.blit(small_font.render("sx:", True, (0, 0, 0)), (770, y_offset + 50))
        screen.blit(small_font.render("sy:", True, (0, 0, 0)), (890, y_offset + 50))
        screen.blit(small_font.render("sz:", True, (0, 0, 0)), (1010, y_offset + 50))
        screen.blit(small_font.render("Угол (°):", True, (0, 0, 0)), (720, y_offset + 140))
        screen.blit(small_font.render("Точка 1 (x,y,z):", True, (0, 0, 0)), (650, y_offset + 365))
        screen.blit(small_font.render("Точка 2 (x,y,z):", True, (0, 0, 0)), (650, y_offset + 400))
        screen.blit(small_font.render("Угол (°):", True, (0, 0, 0)), (650, y_offset + 435))

        # Поля ввода
        for key, rect in input_rects.items():
            input_box(screen, small_font, rect, input_boxes[key], active_input == key)

        # Кнопки преобразований
        if button(screen, font, transform_buttons[0], "Перенос") and button_clicked:
            try:
                dx = float(input_boxes["translation_x"])
                dy = float(input_boxes["translation_y"])
                dz = float(input_boxes["translation_z"])
                main_object.apply_transformation(translation_matrix(dx, dy, dz))
                rendered_object = render_object(main_object, renders[current_render], window_info)
            except ValueError:
                pass
            button_clicked = False

        if button(screen, font, transform_buttons[1], "Масштаб") and button_clicked:
            try:
                sx = float(input_boxes["scale_x"])
                sy = float(input_boxes["scale_y"])
                sz = float(input_boxes["scale_z"])
                scale_relative_to_center(main_object, sx, sy, sz)
                rendered_object = render_object(main_object, renders[current_render], window_info)
            except ValueError:
                pass
            button_clicked = False

        if button(screen, font, transform_buttons[2], "Поворот X") and button_clicked:
            try:
                angle = np.radians(float(input_boxes["rotation_angle"]) / 2)
                rotate_around_center(main_object, 'X', angle)
                rendered_object = render_object(main_object, renders[current_render], window_info)
            except ValueError:
                pass
            button_clicked = False

        if button(screen, font, transform_buttons[3], "Поворот Y") and button_clicked:
            try:
                angle = np.radians(float(input_boxes["rotation_angle"]) / 2)
                rotate_around_center(main_object, 'Y', angle)
                rendered_object = render_object(main_object, renders[current_render], window_info)
            except ValueError:
                pass
            button_clicked = False

        if button(screen, font, transform_buttons[4], "Поворот Z") and button_clicked:
            try:
                angle = np.radians(float(input_boxes["rotation_angle"]) / 2)
                rotate_around_center(main_object, 'Z', angle)
                rendered_object = render_object(main_object, renders[current_render], window_info)
            except ValueError:
                pass
            button_clicked = False

        if button(screen, font, transform_buttons[5], "Отражение XY") and button_clicked:
            main_object.apply_transformation(reflection_xy_matrix())
            rendered_object = render_object(main_object, renders[current_render], window_info)
            button_clicked = False

        if button(screen, font, transform_buttons[6], "Отражение XZ") and button_clicked:
            main_object.apply_transformation(reflection_xz_matrix())
            rendered_object = render_object(main_object, renders[current_render], window_info)
            button_clicked = False

        if button(screen, font, transform_buttons[7], "Отражение YZ") and button_clicked:
            main_object.apply_transformation(reflection_yz_matrix())
            rendered_object = render_object(main_object, renders[current_render], window_info)
            button_clicked = False

        if button(screen, font, transform_buttons[8], "Поворот вокруг прямой") and button_clicked:
            try:
                # Парсим координаты точек
                p1_coords = [float(x.strip()) for x in input_boxes["custom_line_p1"].split(',')]
                p2_coords = [float(x.strip()) for x in input_boxes["custom_line_p2"].split(',')]
                angle = np.radians(float(input_boxes["custom_rotation_angle"]))

                if len(p1_coords) == 3 and len(p2_coords) == 3:
                    p1 = Point(p1_coords[0], p1_coords[1], p1_coords[2])
                    p2 = Point(p2_coords[0], p2_coords[1], p2_coords[2])
                    rotate_around_line(main_object, p1, p2, angle)
                    rendered_object = render_object(main_object, renders[current_render], window_info)
            except ValueError:
                pass
            button_clicked = False

        if button(screen, font, transform_buttons[9], "Сброс") and button_clicked:
            main_object = objects[current_object].create()
            rendered_object = render_object(main_object, renders[current_render], window_info)
            button_clicked = False

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    task()