"""Главный класс редактора полигонов"""
import pygame
import math
from typing import List, Optional, Tuple
import config
from polygon import Polygon
from transformations import translation_matrix, rotation_matrix, scaling_matrix
from geometry import (line_intersection, point_position_relative_to_edge,
                      point_in_polygon, point_to_segment_distance)


class PolygonEditor:
    """Редактор полигонов с поддержкой аффинных преобразований"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
        pygame.display.set_caption("Polygon Editor")
        self.clock = pygame.time.Clock()
        self.running = True

        # Списки полигонов
        self.polygons: List[Polygon] = []
        self.current_polygon: Optional[Polygon] = None
        self.selected_polygon: Optional[Polygon] = None

        # Режимы работы
        self.mode = "create"

        # Временные данные для операций
        self.temp_point: Optional[Tuple[float, float]] = None
        self.temp_edge_start: Optional[Tuple[float, float]] = None
        self.intersection_edge: Optional[Polygon] = None
        self.intersection_point: Optional[Tuple[float, float]] = None

        # UI компоненты
        self.font = pygame.font.Font(None, config.FONT_SIZE)
        self.small_font = pygame.font.Font(None, config.SMALL_FONT_SIZE)

        # Система ввода текста
        self.input_active = False
        self.input_text = ""
        self.input_prompt = ""
        self.input_callback = None
        self.input_params = {}

        # Система сообщений
        self.messages: List[str] = []

    def add_message(self, text: str):
        """Добавить сообщение в лог"""
        self.messages.append(text)
        if len(self.messages) > config.MAX_MESSAGES:
            self.messages.pop(0)

    def start_input(self, prompt: str, callback, **params):
        """Начать режим ввода текста"""
        self.input_active = True
        self.input_text = ""
        self.input_prompt = prompt
        self.input_callback = callback
        self.input_params = params

    def finish_polygon(self):
        """Завершить создание текущего полигона"""
        if self.current_polygon and len(self.current_polygon.vertices) > 0:
            self.polygons.append(self.current_polygon)
            self.current_polygon = None

    def select_polygon_at(self, x: float, y: float) -> Optional[Polygon]:
        """Выбрать полигон в точке (x, y)"""
        for poly in reversed(self.polygons):
            if len(poly.vertices) >= 3:
                # Проверка для полигона
                if point_in_polygon((x, y), poly.vertices):
                    return poly
            elif len(poly.vertices) == 2:
                # Проверка для ребра
                dist = point_to_segment_distance((x, y), poly.vertices[0], poly.vertices[1])
                if dist < config.SELECTION_THRESHOLD:
                    return poly
            elif len(poly.vertices) == 1:
                # Проверка для точки
                dx = x - poly.vertices[0][0]
                dy = y - poly.vertices[0][1]
                if math.sqrt(dx * dx + dy * dy) < config.SELECTION_THRESHOLD:
                    return poly
        return None

    def handle_events(self):
        """Обработка событий pygame"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                self.handle_keydown(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.handle_mouse_click(event.pos)

    def handle_keydown(self, event):
        """Обработка нажатий клавиш"""
        if self.input_active:
            if event.key == pygame.K_RETURN:
                self.input_active = False
                if self.input_callback:
                    self.input_callback(self.input_text, **self.input_params)
            elif event.key == pygame.K_ESCAPE:
                self.input_active = False
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            else:
                self.input_text += event.unicode
        else:
            self.handle_mode_switch(event)

    def handle_mode_switch(self, event):
        """Переключение режимов работы"""
        if event.key == pygame.K_RETURN:
            self.finish_polygon()
        elif event.key == pygame.K_c:
            self.clear_scene()
        elif event.key == pygame.K_1:
            self.switch_to_create_mode()
        elif event.key == pygame.K_2:
            self.switch_to_translate_mode()
        elif event.key == pygame.K_3:
            self.switch_to_rotate_point_mode()
        elif event.key == pygame.K_4:
            self.switch_to_rotate_center_mode()
        elif event.key == pygame.K_5:
            self.switch_to_scale_point_mode()
        elif event.key == pygame.K_6:
            self.switch_to_scale_center_mode()
        elif event.key == pygame.K_7:
            self.switch_to_intersection_mode()
        elif event.key == pygame.K_8:
            self.switch_to_point_in_poly_mode()
        elif event.key == pygame.K_9:
            self.switch_to_classify_mode()

    def clear_scene(self):
        """Очистить сцену"""
        self.polygons.clear()
        self.current_polygon = None
        self.selected_polygon = None
        self.intersection_point = None
        self.add_message("Сцена очищена")

    def switch_to_create_mode(self):
        self.mode = "create"
        self.finish_polygon()
        self.add_message("Режим: создание полигонов")

    def switch_to_translate_mode(self):
        self.mode = "translate"
        self.add_message("Режим: смещение (выберите полигон)")

    def switch_to_rotate_point_mode(self):
        self.mode = "rotate_point"
        self.add_message("Режим: поворот вокруг точки")

    def switch_to_rotate_center_mode(self):
        self.mode = "rotate_center"
        self.add_message("Режим: поворот вокруг центра")

    def switch_to_scale_point_mode(self):
        self.mode = "scale_point"
        self.add_message("Режим: масштабирование от точки")

    def switch_to_scale_center_mode(self):
        self.mode = "scale_center"
        self.add_message("Режим: масштабирование от центра")

    def switch_to_intersection_mode(self):
        self.mode = "intersection"
        self.intersection_edge = None
        self.temp_edge_start = None
        self.add_message("Режим: пересечение ребер (выберите первое ребро)")

    def switch_to_point_in_poly_mode(self):
        self.mode = "point_in_poly"
        self.add_message("Режим: точка в полигоне")

    def switch_to_classify_mode(self):
        self.mode = "classify"
        self.intersection_edge = None
        self.add_message("Режим: классификация точки (выберите ребро)")

    def handle_mouse_click(self, pos: Tuple[int, int]):
        """Обработка кликов мыши в зависимости от режима"""
        x, y = pos

        if self.mode == "create":
            self.handle_create_click(x, y)
        elif self.mode == "translate":
            self.handle_translate_click(x, y)
        elif self.mode == "rotate_point":
            self.handle_rotate_point_click(x, y)
        elif self.mode == "rotate_center":
            self.handle_rotate_center_click(x, y)
        elif self.mode == "scale_point":
            self.handle_scale_point_click(x, y)
        elif self.mode == "scale_center":
            self.handle_scale_center_click(x, y)
        elif self.mode == "intersection":
            self.handle_intersection_click(x, y)
        elif self.mode == "point_in_poly":
            self.handle_point_in_poly_click(x, y)
        elif self.mode == "classify":
            self.handle_classify_click(x, y)

    def handle_create_click(self, x: float, y: float):
        """Обработка клика в режиме создания"""
        if self.current_polygon is None:
            self.current_polygon = Polygon()
        self.current_polygon.add_vertex(x, y)

    def handle_translate_click(self, x: float, y: float):
        """Обработка клика в режиме смещения"""
        poly = self.select_polygon_at(x, y)
        if poly:
            self.selected_polygon = poly
            self.start_input("Введите dx,dy:", self.apply_translation)

    def handle_rotate_point_click(self, x: float, y: float):
        """Обработка клика в режиме поворота вокруг точки"""
        poly = self.select_polygon_at(x, y)
        if poly:
            self.selected_polygon = poly
            self.temp_point = None
            self.start_input("Кликните точку вращения", self.wait_for_rotation_point)

    def handle_rotate_center_click(self, x: float, y: float):
        """Обработка клика в режиме поворота вокруг центра"""
        poly = self.select_polygon_at(x, y)
        if poly:
            self.selected_polygon = poly
            self.start_input("Введите угол (градусы):", self.apply_rotation_center)

    def handle_scale_point_click(self, x: float, y: float):
        """Обработка клика в режиме масштабирования от точки"""
        poly = self.select_polygon_at(x, y)
        if poly:
            self.selected_polygon = poly
            self.temp_point = None
            self.start_input("Кликните центр масштабирования", self.wait_for_scale_point)

    def handle_scale_center_click(self, x: float, y: float):
        """Обработка клика в режиме масштабирования от центра"""
        poly = self.select_polygon_at(x, y)
        if poly:
            self.selected_polygon = poly
            self.start_input("Введите sx,sy:", self.apply_scale_center)

    def handle_intersection_click(self, x: float, y: float):
        """Обработка клика в режиме поиска пересечений"""
        if self.intersection_edge is None:
            poly = self.select_polygon_at(x, y)
            if poly and len(poly.vertices) >= 2:
                self.intersection_edge = poly
                self.temp_edge_start = None
                self.add_message("Первое ребро выбрано. Кликните для второго.")
        elif self.temp_edge_start is None:
            self.temp_edge_start = (x, y)
            self.add_message("Начало второго ребра. Кликните конец.")
        else:
            if len(self.intersection_edge.vertices) >= 2:
                intersection = line_intersection(
                    self.intersection_edge.vertices[0],
                    self.intersection_edge.vertices[1],
                    self.temp_edge_start,
                    (x, y)
                )
                if intersection:
                    self.intersection_point = intersection
                    self.add_message(f"Пересечение: ({intersection[0]:.1f}, {intersection[1]:.1f})")
                else:
                    self.add_message("Ребра не пересекаются")
            self.temp_edge_start = None

    def handle_point_in_poly_click(self, x: float, y: float):
        """Обработка клика в режиме проверки точки в полигоне"""
        poly = self.select_polygon_at(x, y)
        if poly and len(poly.vertices) >= 3:
            inside = point_in_polygon((x, y), poly.vertices)
            self.add_message(f"Точка {'внутри' if inside else 'снаружи'} полигона")

    def handle_classify_click(self, x: float, y: float):
        """Обработка клика в режиме классификации точки"""
        if self.intersection_edge is None:
            poly = self.select_polygon_at(x, y)
            if poly and len(poly.vertices) >= 2:
                self.intersection_edge = poly
                self.add_message("Ребро выбрано. Кликните точку для классификации.")
        else:
            position = point_position_relative_to_edge(
                (x, y),
                self.intersection_edge.vertices[0],
                self.intersection_edge.vertices[1]
            )
            self.add_message(f"Точка находится {position} от ребра")

    def wait_for_rotation_point(self, text, **params):
        """Ожидание клика для выбора точки вращения"""
        waiting = True
        while waiting and self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    waiting = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.temp_point = event.pos
                        waiting = False
                        self.start_input("Введите угол (градусы):", self.apply_rotation_point)

            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

    def wait_for_scale_point(self, text, **params):
        """Ожидание клика для выбора центра масштабирования"""
        waiting = True
        while waiting and self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    waiting = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.temp_point = event.pos
                        waiting = False
                        self.start_input("Введите sx,sy:", self.apply_scale_point)

            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

    # Функции применения преобразований

    def apply_translation(self, text, **params):
        """Применить смещение"""
        try:
            parts = text.split(',')
            dx = float(parts[0])
            dy = float(parts[1])

            if self.selected_polygon:
                matrix = translation_matrix(dx, dy)
                self.selected_polygon.apply_transformation(matrix)
                self.add_message(f"Смещение на ({dx}, {dy}) применено")
        except:
            self.add_message("Ошибка ввода")

    def apply_rotation_point(self, text, **params):
        """Применить поворот вокруг точки"""
        try:
            angle = math.radians(float(text))

            if self.selected_polygon and self.temp_point:
                matrix = rotation_matrix(angle, self.temp_point[0], self.temp_point[1])
                self.selected_polygon.apply_transformation(matrix)
                self.add_message(f"Поворот на {text}° применен")
        except:
            self.add_message("Ошибка ввода")

    def apply_rotation_center(self, text, **params):
        """Применить поворот вокруг центра"""
        try:
            angle = math.radians(float(text))

            if self.selected_polygon:
                cx, cy = self.selected_polygon.get_center()
                matrix = rotation_matrix(angle, cx, cy)
                self.selected_polygon.apply_transformation(matrix)
                self.add_message(f"Поворот на {text}° вокруг центра")
        except:
            self.add_message("Ошибка ввода")

    def apply_scale_point(self, text, **params):
        """Применить масштабирование от точки"""
        try:
            parts = text.split(',')
            sx = float(parts[0])
            sy = float(parts[1])

            if self.selected_polygon and self.temp_point:
                matrix = scaling_matrix(sx, sy, self.temp_point[0], self.temp_point[1])
                self.selected_polygon.apply_transformation(matrix)
                self.add_message(f"Масштабирование ({sx}, {sy}) применено")
        except:
            self.add_message("Ошибка ввода")

    def apply_scale_center(self, text, **params):
        """Применить масштабирование от центра"""
        try:
            parts = text.split(',')
            sx = float(parts[0])
            sy = float(parts[1])

            if self.selected_polygon:
                cx, cy = self.selected_polygon.get_center()
                matrix = scaling_matrix(sx, sy, cx, cy)
                self.selected_polygon.apply_transformation(matrix)
                self.add_message(f"Масштабирование ({sx}, {sy}) от центра")
        except:
            self.add_message("Ошибка ввода")

    def draw(self):
        """Отрисовка всей сцены"""
        self.screen.fill(config.WHITE)

        # Рисуем все полигоны
        for poly in self.polygons:
            poly.draw(self.screen)

        # Рисуем текущий полигон
        if self.current_polygon:
            self.current_polygon.color = config.GREEN
            self.current_polygon.draw(self.screen)

        # Рисуем выбранный полигон
        if self.selected_polygon:
            old_color = self.selected_polygon.color
            self.selected_polygon.color = config.ORANGE
            self.selected_polygon.draw(self.screen)
            self.selected_polygon.color = old_color

        # Рисуем временное ребро для пересечения
        if self.mode == "intersection" and self.temp_edge_start:
            mouse_pos = pygame.mouse.get_pos()
            pygame.draw.line(self.screen, config.RED, self.temp_edge_start, mouse_pos, 2)

        # Рисуем точку пересечения
        if self.intersection_point:
            pygame.draw.circle(self.screen, config.RED,
                               (int(self.intersection_point[0]), int(self.intersection_point[1])), 8)

        # Рисуем UI
        self.draw_ui()

    def draw_ui(self):
        """Отрисовка пользовательского интерфейса"""
        # UI панель
        ui_rect = pygame.Rect(0, config.HEIGHT - config.UI_HEIGHT, config.WIDTH, config.UI_HEIGHT)
        pygame.draw.rect(self.screen, config.GRAY, ui_rect)
        pygame.draw.rect(self.screen, config.BLACK, ui_rect, 2)

        # Инструкции
        instructions = [
            "1-Создание | 2-Смещение | 3-Поворот(точка) | 4-Поворот(центр)",
            "5-Масштаб(точка) | 6-Масштаб(центр) | 7-Пересечение | 8-Точка в полигоне",
            "9-Классификация | Enter-Завершить полигон | C-Очистить"
        ]

        y_offset = config.HEIGHT - 190
        for instruction in instructions:
            text_surface = self.small_font.render(instruction, True, config.BLACK)
            self.screen.blit(text_surface, (10, y_offset))
            y_offset += 25

        # Текущий режим
        mode_text = self.font.render(f"Режим: {self.mode}", True, config.BLACK)
        self.screen.blit(mode_text, (10, config.HEIGHT - 90))

        # Сообщения
        y_offset = config.HEIGHT - 60
        for msg in self.messages[-3:]:
            msg_surface = self.small_font.render(msg, True, config.BLUE)
            self.screen.blit(msg_surface, (10, y_offset))
            y_offset += 20

        # Поле ввода
        if self.input_active:
            input_rect = pygame.Rect(config.WIDTH // 2 - 200, config.HEIGHT // 2 - 30, 400, 60)
            pygame.draw.rect(self.screen, config.WHITE, input_rect)
            pygame.draw.rect(self.screen, config.BLACK, input_rect, 2)

            prompt_surface = self.small_font.render(self.input_prompt, True, config.BLACK)
            self.screen.blit(prompt_surface, (input_rect.x + 10, input_rect.y + 5))

            input_surface = self.font.render(self.input_text, True, config.BLACK)
            self.screen.blit(input_surface, (input_rect.x + 10, input_rect.y + 30))

    def run(self):
        """Главный цикл программы"""
        while self.running:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()