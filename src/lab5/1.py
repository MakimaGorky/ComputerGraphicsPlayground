import pygame
import math
import random
import os
from typing import List, Tuple, Optional

PIVOT = (-300, -300)  # hold my 🍺

# ===== common.py =====

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
    result.width = screen.get_width()
    result.height = screen.get_height()
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

# ===== L_system.py =====

MAX_STACK_SIZE = 1000
MAX_RULES = 10
MAX_STRING_LENGTH = 100000

class TurtleState:
    def __init__(self):
        self.position = Vector2()
        self.angle = 0.0

class TurtleStack:
    def __init__(self):
        self.data = [TurtleState() for _ in range(MAX_STACK_SIZE)]
        self.top = -1
    
    def push(self, state: TurtleState) -> bool:
        if self.top >= MAX_STACK_SIZE - 1:
            return False
        self.top += 1
        self.data[self.top].position.x = state.position.x
        self.data[self.top].position.y = state.position.y
        self.data[self.top].angle = state.angle
        return True
    
    def pop(self) -> TurtleState:
        if self.top < 0:
            empty = TurtleState()
            empty.position = Vector2(0, 0)
            empty.angle = 0
            return empty
        state = TurtleState()
        state.position.x = self.data[self.top].position.x
        state.position.y = self.data[self.top].position.y
        state.angle = self.data[self.top].angle
        self.top -= 1
        return state
    
    def is_empty(self) -> bool:
        return self.top < 0

class Rule:
    def __init__(self):
        self.predecessor = ''
        self.successor = ''

class LSystem:
    def __init__(self):
        self.axiom = "F"
        self.angle = 25.0
        self.initial_angle = -90.0
        self.step = 10.0
        self.rule_count = 0
        self.rules = [Rule() for _ in range(MAX_RULES)]
        self.pos = Vector2(0.0, 0.0)
        
        self.max_iter = 4
        self.angle_variation = 9.0
        self.angle_variations = None
        self.variations_count = 0
        self.use_random = False
        
        self.initial_thickness = 5.0
        self.thickness_decay = 0.65
        self.trunk_color = Color(0, 0, 0, 255)
        self.leaf_color = Color(20, 17, 13, 255)
        self.stack = TurtleStack()

def lsystem_init(ls: LSystem):
    ls.axiom = "F"
    ls.angle = 25.0
    ls.initial_angle = -90.0
    ls.step = 10.0
    ls.rule_count = 0
    ls.pos = Vector2(0.0, 0.0)
    
    ls.max_iter = 4
    ls.angle_variation = 9.0
    ls.angle_variations = None
    ls.variations_count = 0
    ls.use_random = False
    
    ls.initial_thickness = 5.0
    ls.thickness_decay = 0.65
    ls.trunk_color = Color(101, 67, 33, 255)
    ls.leaf_color = Color(60, 179, 113, 255)
    ls.stack = TurtleStack()

def lsystem_load_from_file(ls: LSystem, filename: str) -> bool:
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
        if not lines:
            return False
            
        first_line = lines[0].strip()
        parts = first_line.split()
        
        if len(parts) >= 7:
            ls.axiom = parts[0]
            ls.angle = float(parts[1])
            ls.initial_angle = float(parts[2])
            ls.step = float(parts[3])
            ls.pos = Vector2(float(parts[4]), float(parts[5]))
            ls.max_iter = int(parts[6])
        
        ls.rule_count = 0
        
        for line in lines[1:]:
            line = line.strip()
            if '->' in line and ls.rule_count < MAX_RULES:
                arrow_index = line.find('->')
                predecessor = line[0]
                successor = line[arrow_index + 2:]
                
                ls.rules[ls.rule_count].predecessor = predecessor
                ls.rules[ls.rule_count].successor = successor
                ls.rule_count += 1
                
        return True
        
    except Exception as e:
        print(f"Error loading L-system from file {filename}: {e}")
        return False

def lsystem_generate_string(ls: LSystem, iterations: int) -> str:
    current = ls.axiom
    
    for _ in range(iterations):
        next_str = ""
        
        for symbol in current:
            rule_applied = False
            
            for r in range(ls.rule_count):
                if ls.rules[r].predecessor == symbol:
                    next_str += ls.rules[r].successor
                    rule_applied = True
                    break
            
            if not rule_applied:
                next_str += symbol
        
        current = next_str
        if len(current) > MAX_STRING_LENGTH:
            break
    
    return current


def lsystem_regenerate_variations(ls: LSystem, lstring: str):
    if ls.angle_variations is not None:
        ls.angle_variations = None
    
    if not lstring:
        ls.variations_count = 0
        return
    
    ls.variations_count = len(lstring)
    ls.angle_variations = [random.uniform(-ls.angle_variation, ls.angle_variation) for _ in range(ls.variations_count)]

def lsystem_draw(screen, ls: LSystem, lstring: str):
    if not lstring:
        return
    
    base_step = ls.step
    current_pos = Vector2(ls.pos.x, ls.pos.y)
    current_angle = ls.initial_angle
    
    ls.stack = TurtleStack()
    variation_index = 0
    
    for i, symbol in enumerate(lstring):
        angle_var = 0.0
        
        if (ls.use_random and 
            ls.angle_variations is not None and 
            variation_index < ls.variations_count and
            (symbol == '+' or symbol == '-')):
            
            angle_var = ls.angle_variations[variation_index]
            variation_index += 1
        
        if symbol == 'F':
            new_pos = Vector2(
                current_pos.x + math.cos(math.radians(current_angle)) * base_step,
                current_pos.y + math.sin(math.radians(current_angle)) * base_step
            )
            
            # Отрисовка линии
            pygame.draw.line(screen, (0, 0, 0), 
                           (int(current_pos.x) + PIVOT[0], int(current_pos.y) + PIVOT[1]), 
                           (int(new_pos.x) + PIVOT[0], int(new_pos.y) + PIVOT[1]), 2)
            current_pos = new_pos
            
        elif symbol == 'G':
            new_pos = Vector2(
                current_pos.x + math.cos(math.radians(current_angle)) * base_step,
                current_pos.y + math.sin(math.radians(current_angle)) * base_step
            )
            current_pos = new_pos
            
        elif symbol == '+':
            current_angle += ls.angle + angle_var
            
        elif symbol == '-':
            current_angle -= ls.angle + angle_var
            
        elif symbol == '[':
            state = TurtleState()
            state.position = Vector2(current_pos.x, current_pos.y)
            state.angle = current_angle
            ls.stack.push(state)
            
        elif symbol == ']':
            if not ls.stack.is_empty():
                state = ls.stack.pop()
                current_pos = state.position
                current_angle = state.angle

def lsystem_free(ls: LSystem):
    ls.angle_variations = None
    ls.variations_count = 0

def lsystem_draw_tree(screen, ls: LSystem, lstring: str):
    if not lstring:
        return
    
    base_step = ls.step
    current_pos = Vector2(ls.pos.x, ls.pos.y)
    current_angle = ls.initial_angle
    current_thickness = ls.initial_thickness
    ls.stack = TurtleStack()
    
    thickness_stack = [0.0] * MAX_STACK_SIZE
    thickness_top = -1
    
    for i, symbol in enumerate(lstring):
        angle_var = 0.0
        if (ls.use_random and 
            ls.angle_variations is not None and 
            i < ls.variations_count):
            angle_var = ls.angle_variations[i]
        
        if symbol == 'F':
            new_pos = Vector2(
                current_pos.x + math.cos(math.radians(current_angle)) * base_step,
                current_pos.y + math.sin(math.radians(current_angle)) * base_step
            )
            
            color_ratio = current_thickness / ls.initial_thickness
            
            if color_ratio > 0.6:
                line_color = (ls.trunk_color.r, ls.trunk_color.g, ls.trunk_color.b)
            elif color_ratio < 0.25:
                line_color = (ls.leaf_color.r, ls.leaf_color.g, ls.leaf_color.b)
            else:
                transition_ratio = (color_ratio - 0.25) / (0.6 - 0.25)
                r = int(ls.trunk_color.r * transition_ratio + ls.leaf_color.r * (1.0 - transition_ratio))
                g = int(ls.trunk_color.g * transition_ratio + ls.leaf_color.g * (1.0 - transition_ratio))
                b = int(ls.trunk_color.b * transition_ratio + ls.leaf_color.b * (1.0 - transition_ratio))
                line_color = (r, g, b)
            
            # Отрисовка толстой линии
            thickness = max(1, int(current_thickness))
            pygame.draw.line(screen, line_color,
                           (int(current_pos.x), int(current_pos.y)),
                           (int(new_pos.x), int(new_pos.y)),
                           thickness)
            
            current_pos = new_pos
            
        elif symbol == 'G':
            new_pos = Vector2(
                current_pos.x + math.cos(math.radians(current_angle)) * base_step,
                current_pos.y + math.sin(math.radians(current_angle)) * base_step
            )
            current_pos = new_pos
            
        elif symbol == '+':
            current_angle += ls.angle + angle_var
            
        elif symbol == '-':
            current_angle -= ls.angle + angle_var
            
        elif symbol == '[':
            state = TurtleState()
            state.position = Vector2(current_pos.x, current_pos.y)
            state.angle = current_angle
            ls.stack.push(state)
            
            if thickness_top < MAX_STACK_SIZE - 1:
                thickness_top += 1
                thickness_stack[thickness_top] = current_thickness
            
            current_thickness *= ls.thickness_decay
            
        elif symbol == ']':
            if not ls.stack.is_empty():
                state = ls.stack.pop()
                current_pos = state.position
                current_angle = state.angle
                
                if thickness_top >= 0:
                    current_thickness = thickness_stack[thickness_top]
                    thickness_top -= 1

# ===== main.py =====

class FractalOption:
    def __init__(self, name: str, filename: str):
        self.name = name
        self.filename = filename

def task1():
    pygame.init()
    
    # Полноэкранный режим
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("L-systems")
    
    info = pygame.display.Info()
    task_window_width = info.current_w
    task_window_height = info.current_h
    
    ls = LSystem()
    lsystem_init(ls)
    
    # Используем абсолютные пути или создаем тестовые файлы
    fractals = [
        FractalOption("Кривая Коха", "./fractals/koch.txt"),
        FractalOption("Снежинка Коха", "./fractals/snowflake.txt"),
        FractalOption("Квадратный остров Коха", "./fractals/island.txt"),
        FractalOption("Дракон", "./fractals/dragon.txt"),
        FractalOption("Дракон Хартера-Хейтуэя", "./fractals/dragon2.txt"),
        FractalOption("Куст 1", "./fractals/tree1.txt"),
        FractalOption("Куст 2", "./fractals/tree2.txt"),
        FractalOption("Куст 3", "./fractals/tree3.txt"),
        FractalOption("Треугольник Серпинского", "./fractals/sierpinski_carpet.txt"),
        # FractalOption("Наконечник Серпинского", "./fractals/peak.txt"),
        # FractalOption("Кривая Гилберта", "./fractals/gilbert_curve.txt"),
        # FractalOption("Кривая Госпера", "./fractals/gosper_curve.txt"),
        # FractalOption("Шестиугольная мозаика", "./fractals/mosaic.txt")
    ]
    
    fractal_count = len(fractals)
    current_fractal = 0
    iterations = 1
    show_dropdown = False
    ui_background_color = (220, 220, 220)
    
    font = pygame.font.Font(None, 36)
    
    dropdown_bounds = Rectangle(20, 20, 250, 40)
    iter_minus_button = Rectangle(280, 20, 40, 40)
    iter_plus_button = Rectangle(330, 20, 40, 40)
    random_button = Rectangle(380, 20, 200, 40)
    regenerate_button = Rectangle(590, 20, 250, 40)
    
    lstring = ""
    
    # Создаем тестовый фрактал если файлы не найдены
    if not os.path.exists(fractals[current_fractal].filename):
        print("Файлы фракталов не найдены, используем тестовый L-систему...")
        ls.axiom = "F"
        ls.angle = 25.0
        ls.initial_angle = -90.0
        ls.step = 50.0
        ls.pos = Vector2(task_window_width // 2, task_window_height - 100)
        ls.max_iter = 4
        ls.rule_count = 1
        ls.rules[0].predecessor = 'F'
        ls.rules[0].successor = 'F[+F]F[-F]F'
    
    if lsystem_load_from_file(ls, fractals[current_fractal].filename):
        lstring = lsystem_generate_string(ls, iterations)
    else:
        # Если файл не загрузился, генерируем строку из тестовой системы
        lstring = lsystem_generate_string(ls, iterations)
    
    last_fractal = -1
    
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
        
        # Отрисовка кнопок
        mouse_pressed = pygame.mouse.get_pressed()[0]
        
        # Выпадающий список
        if button(screen, font, dropdown_bounds, fractals[current_fractal].name) and button_clicked:
            show_dropdown = not show_dropdown
            button_clicked = False
        
        if show_dropdown:
            button_cnt = 1
            for i in range(fractal_count):
                if i == current_fractal:
                    continue
                option_rect = Rectangle(
                    dropdown_bounds.x,
                    dropdown_bounds.y + button_cnt * 50,
                    dropdown_bounds.width,
                    dropdown_bounds.height
                )
                if button(screen, font, option_rect, fractals[i].name) and button_clicked:
                    current_fractal = i
                    show_dropdown = False
                    iterations = 1
                    if lsystem_load_from_file(ls, fractals[current_fractal].filename):
                        lstring = lsystem_generate_string(ls, iterations)
                    button_clicked = False
                button_cnt += 1
        
        if current_fractal != last_fractal:
            lsystem_free(ls)
            if lsystem_load_from_file(ls, fractals[current_fractal].filename):
                lstring = lsystem_generate_string(ls, iterations)
            last_fractal = current_fractal
        
        # Кнопки итераций
        if button(screen, font, iter_minus_button, "-") and button_clicked and iterations > 1:
            iterations -= 1
            lstring = lsystem_generate_string(ls, iterations)
            button_clicked = False
        
        if button(screen, font, iter_plus_button, "+") and button_clicked and iterations < ls.max_iter:
            iterations += 1
            lstring = lsystem_generate_string(ls, iterations)
            button_clicked = False
        
        # Кнопка случайных вариаций
        random_text = "Вариации: ВКЛ" if ls.use_random else "Вариации: ВЫКЛ"
        if button(screen, font, random_button, random_text) and button_clicked:
            ls.use_random = not ls.use_random
            if ls.use_random:
                lsystem_regenerate_variations(ls, lstring)
            button_clicked = False
        
        # Кнопка регенерации вариаций
        if ls.use_random and button(screen, font, regenerate_button, "Новые вариации") and button_clicked:
            lsystem_regenerate_variations(ls, lstring)
            button_clicked = False
        
        # Отрисовка фрактала по центру экрана
        if lstring:
            # Сохраняем текущую позицию и временно меняем для отрисовки
            original_pos = Vector2(ls.pos.x, ls.pos.y)
            ls.pos = Vector2(task_window_width // 2, task_window_height - 100)
            
            if 5 <= current_fractal <= 7:  # Кусты (индексы 5-7)
                lsystem_draw_tree(screen, ls, lstring)
            else:
                lsystem_draw(screen, ls, lstring)
            
            # Восстанавливаем оригинальную позицию
            ls.pos = original_pos
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    task1()