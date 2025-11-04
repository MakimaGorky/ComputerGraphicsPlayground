import pygame
import math
import random
import os
import config
import numpy as np
from typing import List, Tuple, Optional


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

class Histogram:
    def __init__(self):
        self.values = []
        self.bar_count = 0
        self.bounds = Rectangle()
        self.color = Color()

def get_window_info(screen) -> WindowInfo:
    result = WindowInfo()
    result.width = screen.Info().current_w
    result.height = screen.Info().current_h
    result.center.x = result.width / 2.0
    result.center.y = result.height / 2.0
    return result

def draw_texture_centered(screen, texture, x: float, y: float):
    x -= texture.get_width() / 2.0
    y -= texture.get_height() / 2.0
    screen.blit(texture, (x, y))

def draw_text_centered(screen, font, text: str, x: float, y: float, color: Color):
    lines = text.split('\n')
    total_text_height = 0.0
    
    for line in lines:
        text_surface = font.render(line, True, (color.r, color.g, color.b))
        total_text_height += text_surface.get_height()
    
    y -= total_text_height / 2.0
    
    for line in lines:
        text_surface = font.render(line, True, (color.r, color.g, color.b))
        text_x = x - text_surface.get_width() / 2.0
        text_y = y
        screen.blit(text_surface, (text_x, text_y))
        y += text_surface.get_height()

def button(screen, font, rect: Rectangle, text: str) -> bool:
    mouse_pos = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()[0]
    
    is_hovered = (rect.x <= mouse_pos[0] <= rect.x + rect.width and
                  rect.y <= mouse_pos[1] <= rect.y + rect.height)
    
    color = (100, 100, 200) if is_hovered else (70, 70, 170)
    
    pygame.draw.rect(screen, color, (rect.x, rect.y, rect.width, rect.height))
    pygame.draw.rect(screen, (255, 255, 255), (rect.x, rect.y, rect.width, rect.height), 2)
    
    text_surface = font.render(text, True, (255, 255, 255))
    text_x = rect.x + (rect.width - text_surface.get_width()) / 2
    text_y = rect.y + (rect.height - text_surface.get_height()) / 2
    screen.blit(text_surface, (text_x, text_y))
    
    # Возвращаем True если кнопка была нажата и отпущена
    return is_hovered and pygame.mouse.get_pressed()[0]

# ===== 3D Graphics =====

class Point:
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z

class Polygon:
    def __init__(self, points: List[Point] = []):
        self.vertices = points.copy()

    def add_vertex(self, p: Point):
        self.vertices.append(p)

    def get_center(self) -> Point:
        """Вычислить геометрический центр (центроид) полигона"""
        if not self.vertices:
            return (0, 0)

        cx = sum(v.x for v in self.vertices) / len(self.vertices)
        cy = sum(v.y for v in self.vertices) / len(self.vertices)
        cz = sum(v.z for v in self.vertices) / len(self.vertices)
        return Point(cx, cy, cz)

    def apply_transformation(self, matrix: np.ndarray):
        #todo
        pass

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

    def apply_transformation(self, matrix: np.ndarray):
        for p in self.polygons:
            p.apply_transformation(matrix) # Применяем преобразования к каждому полигону. Хз как на самом деле надо

    def __len__(self):
        return len(self.vertices)

    def __iter__(self):
        return iter(self.vertices)

    def __getitem__(self, index):
        return self.vertices[index]

class PolygonProjection:
    def __init__(self, points: List[Tuple[float, float]] = []):
        self.vertices = points.copy()
        self.color = config.BLUE

    def add_vertex(self, x: float, y: float):
        """Добавить вершину в полигон"""
        self.vertices.append((x, y))

    def add_vertex(self, point: Tuple[float, float]):
        """Добавить вершину в полигон"""
        self.vertices.append(point)

    def draw(self, screen):
        """Отрисовка полигона на экране"""
        if len(self.vertices) == 1:
            # Точка
            pygame.draw.circle(screen, self.color,
                               (int(self.vertices[0][0] + PIVOT[0]), int(self.vertices[0][1] + PIVOT[1])),
                               config.POINT_RADIUS)
        elif len(self.vertices) == 2:
            # Ребро
            pygame.draw.line(screen, self.color,
                             (int(self.vertices[0][0] + PIVOT[0]), int(self.vertices[0][1] + PIVOT[1])),
                             (int(self.vertices[1][0] + PIVOT[0]), int(self.vertices[1][1] + PIVOT[1])),
                             config.LINE_WIDTH)
        else:
            # Полигон
            int_vertices = [(int(v[0] + PIVOT[0]), int(v[1] + PIVOT[1])) for v in self.vertices]
            pygame.draw.polygon(screen, self.color, int_vertices, config.LINE_WIDTH)
            # Рисуем вершины
            for v in int_vertices:
                pygame.draw.circle(screen, config.RED, v, config.VERTEX_RADIUS)

    def __len__(self):
        return len(self.vertices)

    def __iter__(self):
        return iter(self.vertices)

    def __getitem__(self, index):
        return self.vertices[index]

def render_point(vertex: Point, method: str, window: WindowInfo):
    vertex_h = np.array([vertex.x, vertex.y, vertex.z + Z_PIVOT, 1])
    
    projection_matrix = []
    if method == "Аксонометрическая":
        a = np.radians(config.ANGLE)
        projection_matrix = [
            [1, 0, 0.5*np.cos(a), 0 ],
            [0, 1, 0.5*np.cos(a), 0],
            [0, 0, 0, 0],
            [0, 0, 0, 1]
        ]
    elif method == "Перспективная":
        c = config.V_POINT
        projection_matrix = [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 0],
            [0, 0, -1/c, 1]
        ]

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
    tetr.add_face(Polygon([
                        vert[1],
                        vert[2],
                        vert[3]
                        ]))

    for i in range(3):
        tetr.add_face(Polygon([
                            vert[0],
                            vert[1+i],
                            vert[1 + (i+1)//3]
                            ]))

    return tetr

def create_octahedron() -> Object:
    cube = create_cube()
    vert = []
    for f in cube.polygons:
        vert.append(f.get_center())

    octa = Object()
    octa.add_face(Polygon([vert[0],
                        vert[1], 
                        vert[4]]))
    octa.add_face(Polygon([vert[5],
                        vert[1], 
                        vert[4]]))
    for i in range(3):
        octa.add_face(Polygon([vert[0],
                            vert[i+1], 
                            vert[i+2]]))
        octa.add_face(Polygon([vert[5],
                            vert[i+1], 
                            vert[i+2]]))
    return octa

def load_object(filename: str) -> Object:
    #todo: load object
    return create_test_cube()

# ===== main.py =====

class ObjectOption:
    def __init__(self, name: str, creator):
        self.name = name
        self.create = creator

def task():
    pygame.init()
    
    # Полноэкранный режим
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("3DRendrer")

    window_info = get_window_info(pygame.display)
    
    ## Заменить на многогранники
    # Используем абсолютные пути или создаем тестовые файлы
    objects = [
        ObjectOption("Тетраэдр", create_tetrahedron),
        ObjectOption("Гексаэдр", create_cube),
        ObjectOption("Октаэдр", create_octahedron),
        ObjectOption("Икосаэдр", None),
        ObjectOption("Додекаэдр", None)
    ]
    
    object_count = len(objects)
    current_object = 0
    show_dropdown_objects = False
    ui_background_color = (220, 220, 220)
    
    font = pygame.font.Font(None, 36)
    
    dropdown_bounds_objects = Rectangle(20, 20, 210, 40)

    renders = [
        "Аксонометрическая",
        "Перспективная"
    ]

    renders_count = len(renders)
    current_render = 0
    show_dropdown_renders = False

    dropdown_bounds_renders = Rectangle(250, 20, 270, 40)
    
    main_object: Optional[Object] = None
    ## Гексаэдр
    # Создаем куб если объекты не найдены
    if not objects[current_object].create:
        print(f"Генератор фигуры {objects[current_object].name} не найден, будет загружен тестовый куб")
        main_object = create_cube()
    else:
        main_object = objects[current_object].create()
    
    rendered_object = render_object(main_object, renders[current_render], window_info)
    
    last_object = -1
    last_render = -1
    
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
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Левая кнопка мыши
                    button_clicked = True
        
        screen.fill(ui_background_color)

        if rendered_object:
            for rp in rendered_object:
                rp.draw(screen)
        
        # Отрисовка кнопок
        mouse_pressed = pygame.mouse.get_pressed()[0]
        
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
                    dropdown_bounds_objects.y + button_cnt * 50,
                    dropdown_bounds_objects.width,
                    dropdown_bounds_objects.height
                )
                if button(screen, font, option_rect, objects[i].name) and button_clicked:
                    current_object = i
                    show_dropdown_objects = False
                    button_clicked = False
                button_cnt += 1
        
        if current_object != last_object:
            if not objects[current_object].create:
                print(f"Генератор фигуры {objects[current_object].name} не найден, будет загружен тестовый куб")
                main_object = create_cube()
            else:
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
                    dropdown_bounds_renders.y + button_cnt * 50,
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
        
        # # Кнопки итераций
        # if button(screen, font, iter_minus_button, "-") and button_clicked and iterations > 1:
        #     iterations -= 1
        #     lstring = lsystem_generate_string(ls, iterations)
        #     button_clicked = False
        
        # if button(screen, font, iter_plus_button, "+") and button_clicked and iterations < ls.max_iter:
        #     iterations += 1
        #     lstring = lsystem_generate_string(ls, iterations)
        #     button_clicked = False
        
        # # Кнопка случайных вариаций
        # random_text = "Вариации: ВКЛ" if ls.use_random else "Вариации: ВЫКЛ"
        # if button(screen, font, random_button, random_text) and button_clicked:
        #     ls.use_random = not ls.use_random
        #     if ls.use_random:
        #         lsystem_regenerate_variations(ls, lstring)
        #     button_clicked = False
        
        # # Кнопка регенерации вариаций
        # if ls.use_random and button(screen, font, regenerate_button, "Новые вариации") and button_clicked:
        #     lsystem_regenerate_variations(ls, lstring)
        #     button_clicked = False
        
        ## Отрисовка объекта
        # # Отрисовка фрактала по центру экрана
        # if lstring:
        #     print("отрисовали object")
            # Сохраняем текущую позицию и временно меняем для отрисовки
            # original_pos = Vector2(ls.pos.x, ls.pos.y)
            # ls.pos = Vector2(task_window_width // 2, task_window_height - 100)
            
            # if 5 <= current_object <= 7:  # Кусты (индексы 5-7)
            #     lsystem_draw_tree(screen, ls, lstring)
            # else:
            #     lsystem_draw(screen, ls, lstring)
            
            # # Восстанавливаем оригинальную позицию
            # ls.pos = original_pos
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    task()