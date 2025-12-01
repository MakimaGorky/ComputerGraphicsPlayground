import pygame
import os
import math
import numpy as np
from datetime import datetime
from typing import List, Tuple, Any

# Импорты модулей проекта
from primitives import *
# from create_test_models import *
from object_IO import *
from D3Renderer import *
from camera import *
from UI import *
from plot import Plot
from rotation_shape import *
import light

# ==========================================
# КОНФИГУРАЦИЯ ИНТЕРФЕЙСА
# ==========================================
WINDOW_WIDTH = 1540
WINDOW_HEIGHT = 900
HALF_WIDTH = WINDOW_WIDTH // 2
HALF_HEIGHT = WINDOW_HEIGHT // 2
SIDEBAR_WIDTH = 360  # Чуть шире для удобства
VIEWPORT_START_X = SIDEBAR_WIDTH
VIEWPORT_WIDTH = WINDOW_WIDTH - SIDEBAR_WIDTH

# Цвета
VIEWPORT_COLOR = (240, 240, 245)
SIDEBAR_COLOR = (50, 55, 65)
TEXT_COLOR = (220, 220, 220)
HEADER_COLOR = (255, 215, 0) # Золотистый для заголовков
OVERLAY_BG = (70, 75, 85)

# Глобальное состояние ввода
input_boxes = {
    "tx": "0", "ty": "0", "tz": "0",
    "sx": "1.1", "sy": "1.1", "sz": "1.1",
    "angle": "15",
    "plot_func": "math.sin(x)*math.cos(y)*2",
    "plot_lims": "-6, 6, -6, 6",
    "plot_n": "40",
    "rot_profile": "(50,0) (80,50) (80,100) (0,150)",
    "rot_iter": "16",
    "filename": "model"
}
active_input = None

class LayoutManager:
    """Класс для автоматического размещения элементов UI вертикально"""
    def __init__(self, start_x, start_y, width):
        self.start_x = start_x
        self.start_y = start_y
        self.current_y = start_y
        self.width = width
        self.padding = 10
        self.line_height = 30 # Чуть компактнее

    def next_pos(self, height=None):
        h = height if height else self.line_height
        rect = Rectangle(self.start_x + self.padding, self.current_y, self.width - 2 * self.padding, h)
        self.current_y += h + 8
        return rect

    def split_row(self, parts, height=None):
        """Разделяет строку на несколько частей"""
        h = height if height else self.line_height
        rects = []
        total_w = self.width - 2 * self.padding
        # parts - это веса ширины, например [1, 2] значит второй элемент в 2 раза шире первого
        total_parts = sum(parts)
        gap = 5
        available_w = total_w - (len(parts) - 1) * gap
        unit_w = available_w / total_parts

        current_x = self.start_x + self.padding
        for p in parts:
            w = p * unit_w
            rects.append(Rectangle(current_x, self.current_y, w, h))
            current_x += w + gap

        self.current_y += h + 8
        return rects

    def add_spacer(self, pixels=15):
        self.current_y += pixels

    def reset(self):
        self.current_y = self.start_y

def draw_text(screen, font, text, x, y, color=TEXT_COLOR):
    surf = font.render(text, True, color)
    screen.blit(surf, (x, y))

def handle_input_logic(event):
    global active_input
    if event.type == pygame.KEYDOWN and active_input:
        if event.key == pygame.K_RETURN:
            active_input = None
        elif event.key == pygame.K_BACKSPACE:
            input_boxes[active_input] = input_boxes[active_input][:-1]
        else:
            input_boxes[active_input] += event.unicode

def app():
    global active_input

    # --- Инициализация путей ---
    current_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(current_dir, 'models')
    if not os.path.exists(models_dir): os.makedirs(models_dir)

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("3D Renderer Studio")

    font = pygame.font.Font(None, 24)
    header_font = pygame.font.Font(None, 30)

    # --- Настройка камеры ---
    # Важно: устанавливаем камеру в центр области просмотра (viewport)
    camera.x = 0
    camera.y = 0
    camera.z = -800 # Начальный Z

    # WindowInfo нужен рендереру (хотя D3Renderer больше полагается на camera.x/y)
    window_info = get_window_info(screen)

    # --- Состояние Приложения ---
    obj_options = [
        ObjectOption("Тетраэдр", create_tetrahedron),
        ObjectOption("Куб", create_cube),
        ObjectOption("Октаэдр", create_octahedron),
        ObjectOption("Икосаэдр", create_icosahedron),
        ObjectOption("Додекаэдр", create_dodecahedron)
    ]
    curr_obj_idx = 1 # Куб по умолчанию

    main_object = obj_options[curr_obj_idx].create()
    scene_objects = [main_object]
    scene_mode = "single"

    render_modes = ["Перспективная", "Аксонометрическая"]
    curr_render_idx = 0

    settings = {
        "zbuffer": True,
        "faces": True,
        "wireframe": True,
        "normals": False,
        "rotate": True
    }

    # UI State
    show_obj_dropdown = False

    clock = pygame.time.Clock()
    layout = LayoutManager(0, 0, SIDEBAR_WIDTH)
    running = True
    
\
    # ==========================
    # ГЛАВНЫЙ ЦИКЛ
    # ==========================
    while running:
        clicked = False
        mouse_pos = pygame.mouse.get_pos()

        # 1. События
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                handle_input_logic(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    clicked = True
                    # Сброс фокуса инпута при клике (если клик не по новому инпуту - обработается ниже)
                    # Если клик был по меню, мы его перехватим позже

        # 2. Логика вращения
        if settings["rotate"]:
            targets = scene_objects if scene_mode == "multiple" else [main_object]
            for obj in targets:
                if obj:
                    rotate_around_center(obj, 'Y', np.radians(0.5))
                    rotate_around_center(obj, 'X', np.radians(0.3))

        camera.update()

        # 3. Отрисовка фона и Viewport
        screen.fill(SIDEBAR_COLOR) # Весь фон темный (подложка сайдбара)
        # Рисуем область просмотра поверх
        pygame.draw.rect(screen, VIEWPORT_COLOR, (VIEWPORT_START_X, 0, VIEWPORT_WIDTH, WINDOW_HEIGHT))

        # 4. Рендеринг 3D сцены
        to_render = [o for o in (scene_objects if scene_mode == "multiple" else [main_object]) if o is not None]

        # Используем функции рендеринга
        # (Они рисуют прямо на screen)
        render_func = render_multiple_objects if scene_mode == "multiple" else render_object

        if scene_mode == "light":
            rendered_polys = light.render_lit_object(screen, scene_objects[0], light.single_light_source, camera.get_pos())
        elif scene_mode == "single" and len(to_render) > 0:
            rendered_polys = render_object(to_render[0], render_modes[curr_render_idx], window_info, settings["zbuffer"])
        elif scene_mode == "multiple":
            rendered_polys = render_multiple_objects(to_render, render_modes[curr_render_idx], window_info, settings["zbuffer"])
        else:
            rendered_polys = []

        if rendered_polys:
            for poly in rendered_polys:
                poly.draw(screen, settings["faces"], settings["wireframe"])
                if settings["normals"]: poly.draw_normal(screen)

        # ==========================
        # ГЕНЕРАЦИЯ UI (САЙДБАР)
        # ==========================
        if clicked:
            active_input = None

        layout.reset()
        layout.add_spacer(15)
        draw_text(screen, header_font, "НАСТРОЙКИ СЦЕНЫ", 20, layout.current_y, HEADER_COLOR)
        layout.add_spacer(25)

        # Переменная для отложенной отрисовки выпадающего меню
        dropdown_to_draw = None

        # --- Выбор объекта ---
        rect_obj = layout.next_pos()
        if button(screen, font, rect_obj, f"Объект: {obj_options[curr_obj_idx].name}") and clicked:
            show_obj_dropdown = not show_obj_dropdown
            clicked = False # Поглощаем клик

        # Если меню открыто, запоминаем его координаты, но не рисуем пока
        if show_obj_dropdown:
            dropdown_to_draw = (rect_obj, obj_options)

        # --- Режим сцены ---
        r_mode, r_add, r_clr = layout.split_row([1, 0.8, 0.8])
        mode_txt = "Режим: МНОГО" if scene_mode == "multiple" else "Режим: ОДИН"
        if button(screen, font, r_mode, mode_txt) and clicked:
            scene_mode = "multiple" if scene_mode == "single" else "single"
            if scene_mode == "single": scene_objects = [main_object]
            else: scene_objects = [main_object]

        if button(screen, font, r_add, "+ Доб.") and clicked:
            if scene_mode == "multiple":
                new_obj = obj_options[curr_obj_idx].create()
                import random
                # Случайное смещение, чтобы видно было новый объект
                dx, dy = random.randint(-200, 200), random.randint(-150, 150)
                new_obj.apply_transformation(translation_matrix(dx, dy, 0))
                scene_objects.append(new_obj)

        if button(screen, font, r_clr, "Очист.") and clicked:
            if scene_mode == "multiple": scene_objects = []

        layout.add_spacer(15)
        draw_text(screen, header_font, "ОТОБРАЖЕНИЕ", 20, layout.current_y, HEADER_COLOR)
        layout.add_spacer(20)

        # --- Рендер и опции ---
        rect_rnd = layout.next_pos()
        if button(screen, font, rect_rnd, f"Вид: {render_modes[curr_render_idx]}") and clicked:
            curr_render_idx = (curr_render_idx + 1) % len(render_modes)

        # Grid of toggles
        row1 = layout.split_row([1, 1])
        if button(screen, font, row1[0], f"Z-Buf: {'ВКЛ' if settings['zbuffer'] else 'ВЫКЛ'}") and clicked:
            settings["zbuffer"] = not settings["zbuffer"]
        if button(screen, font, row1[1], f"Вращ.: {'ВКЛ' if settings['rotate'] else 'ВЫКЛ'}") and clicked:
            settings["rotate"] = not settings["rotate"]

        row2 = layout.split_row([1, 1, 1])
        if button(screen, font, row2[0], f"Грани{' ✔' if settings['faces'] else ''}") and clicked:
            settings['faces'] = not settings['faces']
        if button(screen, font, row2[1], f"Сетка{' ✔' if settings['wireframe'] else ''}") and clicked:
            settings['wireframe'] = not settings['wireframe']
        if button(screen, font, row2[2], f"Норм.{' ✔' if settings['normals'] else ''}") and clicked:
            settings['normals'] = not settings['normals']

        layout.add_spacer(15)
        draw_text(screen, header_font, "ТРАНСФОРМАЦИИ", 20, layout.current_y, HEADER_COLOR)
        layout.add_spacer(20)

        targets = scene_objects if scene_mode == "multiple" else [main_object]

        # --- Move ---
        lbl_t, inp_tx, inp_ty, inp_tz, btn_t = layout.split_row([0.6, 1, 1, 1, 1.2])
        draw_text(screen, font, "Move:", lbl_t.x, lbl_t.y + 8)

        # Helper for inputs
        def handle_input_ui(rect, key):
            is_active = (active_input == key)
            input_box(screen, font, rect, input_boxes[key], is_active)
            if clicked and rect.x < mouse_pos[0] < rect.x+rect.width and rect.y < mouse_pos[1] < rect.y+rect.height:
                return True
            return False

        if handle_input_ui(inp_tx, "tx"): active_input = "tx"
        if handle_input_ui(inp_ty, "ty"): active_input = "ty"
        if handle_input_ui(inp_tz, "tz"): active_input = "tz"

        if button(screen, font, btn_t, "OK") and clicked:
            try:
                mat = translation_matrix(float(input_boxes["tx"]), float(input_boxes["ty"]), float(input_boxes["tz"]))
                for o in targets: o.apply_transformation(mat)
            except: pass

        # --- Scale ---
        lbl_s, inp_sx, inp_sy, inp_sz, btn_s = layout.split_row([0.6, 1, 1, 1, 1.2])
        draw_text(screen, font, "Scale:", lbl_s.x, lbl_s.y + 8)
        if handle_input_ui(inp_sx, "sx"): active_input = "sx"
        if handle_input_ui(inp_sy, "sy"): active_input = "sy"
        if handle_input_ui(inp_sz, "sz"): active_input = "sz"

        if button(screen, font, btn_s, "OK") and clicked:
            try:
                sx, sy, sz = float(input_boxes["sx"]), float(input_boxes["sy"]), float(input_boxes["sz"])
                for o in targets: scale_relative_to_center(o, sx, sy, sz)
            except: pass

        # --- Rotate ---
        lbl_r, inp_ang, btn_rx, btn_ry, btn_rz = layout.split_row([0.8, 1, 0.7, 0.7, 0.7])
        draw_text(screen, font, "Rot(°):", lbl_r.x, lbl_r.y + 8)
        if handle_input_ui(inp_ang, "angle"): active_input = "angle"

        try: ang = np.radians(float(input_boxes["angle"]))
        except: ang = 0

        if button(screen, font, btn_rx, "X") and clicked:
            for o in targets: rotate_around_center(o, 'X', ang)
        if button(screen, font, btn_ry, "Y") and clicked:
            for o in targets: rotate_around_center(o, 'Y', ang)
        if button(screen, font, btn_rz, "Z") and clicked:
            for o in targets: rotate_around_center(o, 'Z', ang)

        layout.add_spacer(15)
        draw_text(screen, header_font, "ГЕНЕРАТОРЫ", 20, layout.current_y, HEADER_COLOR)
        layout.add_spacer(20)

        # --- Plot ---
        draw_text(screen, font, "f(x,y) =", 20, layout.current_y)
        layout.next_pos(10) # offset
        rect_f = layout.next_pos()
        if handle_input_ui(rect_f, "plot_func"): active_input = "plot_func"

        r_lim_lbl, r_lim_inp, r_n_lbl, r_n_inp = layout.split_row([0.8, 2, 0.5, 0.8])
        draw_text(screen, font, "Lims:", r_lim_lbl.x, r_lim_lbl.y+8)
        if handle_input_ui(r_lim_inp, "plot_lims"): active_input = "plot_lims"
        draw_text(screen, font, "N:", r_n_lbl.x, r_n_lbl.y+8)
        if handle_input_ui(r_n_inp, "plot_n"): active_input = "plot_n"

        if button(screen, font, layout.next_pos(), "Построить График") and clicked:
            try:
                p_func = lambda x, y: eval(input_boxes["plot_func"], {"x": x, "y": y, "math": math})
                lims = [float(v) for v in input_boxes["plot_lims"].split(',')]
                n_p = int(input_boxes["plot_n"])
                plot_obj = Plot(p_func, ((lims[0], lims[1]), (lims[2], lims[3])), n_p)
                path = os.path.join(models_dir, "_temp.obj")
                plot_obj.export(path)
                main_object = load_obj(path)
                if scene_mode == "single": scene_objects = [main_object]
            except Exception as e: print(e)

        # --- Revolution ---
        layout.add_spacer(5)
        draw_text(screen, font, "Профиль вращения (x,y):", 20, layout.current_y)
        layout.next_pos(10)
        rect_prof = layout.next_pos()
        if handle_input_ui(rect_prof, "rot_profile"): active_input = "rot_profile"

        r_iter_lbl, r_iter_inp, r_rot_btn = layout.split_row([1, 0.8, 1.5])
        draw_text(screen, font, "Сегменты:", r_iter_lbl.x, r_iter_lbl.y+8)
        if handle_input_ui(r_iter_inp, "rot_iter"): active_input = "rot_iter"

        if button(screen, font, r_rot_btn, "Создать тело") and clicked:
            try:
                dots = get_dots_from_string(input_boxes["rot_profile"])
                it = int(input_boxes["rot_iter"])
                main_object = create_solid_of_revolution(dots, it)
                if scene_mode == "single": scene_objects = [main_object]
            except Exception as e: print(e)

        layout.add_spacer(15)

        # --- File I/O ---
        r_fn, r_load, r_save = layout.split_row([1.5, 0.8, 0.8])
        if handle_input_ui(r_fn, "filename"): active_input = "filename"
        if button(screen, font, r_load, "Загрузить") and clicked:
            try:
                path = os.path.join(models_dir, input_boxes["filename"]+".obj")
                lit_model = light.LitObject.from_obj(path, color=(0.8, 0.4, 0.4), scale=50.0)
                # main_object = load_obj(path)
                main_object = lit_model
                if scene_mode == "single": scene_objects = [main_object]
                scene_mode = 'light'
            except: print("Error loading")
        if button(screen, font, r_save, "Сохр.") and clicked:
            try:
                path = os.path.join(models_dir, f"saved_{datetime.now().strftime('%H%M%S')}.obj")
                save_obj(main_object, path)
            except: pass

        # ==================================================
        # ОТРИСОВКА ВСПЛЫВАЮЩИХ ОКОН (OVERLAY)
        # Рисуем их в самом конце, чтобы они перекрывали всё
        # ==================================================
        if dropdown_to_draw:
            parent_rect, options = dropdown_to_draw
            item_h = 35
            total_h = len(options) * item_h

            # Рисуем подложку
            dropdown_bg_rect = (parent_rect.x, parent_rect.y + parent_rect.height, parent_rect.width, total_h)
            pygame.draw.rect(screen, OVERLAY_BG, dropdown_bg_rect)
            pygame.draw.rect(screen, TEXT_COLOR, dropdown_bg_rect, 1) # Рамка

            for i, opt in enumerate(options):
                opt_rect = Rectangle(parent_rect.x, parent_rect.y + parent_rect.height + i * item_h, parent_rect.width, item_h)

                # Используем button(), но с проверкой клика здесь же
                if button(screen, font, opt_rect, opt.name) and clicked:
                    curr_obj_idx = i
                    main_object = obj_options[curr_obj_idx].create()
                    if scene_mode == "single": scene_objects = [main_object]
                    show_obj_dropdown = False
                    clicked = False # Клик обработан

            # Если кликнули мимо списка, закрываем его
            if clicked:
                show_obj_dropdown = False

        # Сброс клика в конце кадра, если он никем не обработан
        # if clicked and active_input and not any(rect.collidepoint(mouse_pos) for rect in [input_boxes.get(k) for k in input_boxes if isinstance(input_boxes.get(k), pygame.Rect)]):
        #     active_input = None

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    app()