import pygame
from primitives import *
from create_test_models import *
from datetime import datetime
from object_IO import *
from D3Renderer import *
from camera import *
import os
import math
from plot import Plot
from rotation_shape import *

FULLSCREEN = False

def app():
    current_file_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file_path)
    models_dir = os.path.join(current_dir, 'models')
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)

    pygame.init()

    screen = pygame.display.set_mode((1400, 900))
    if FULLSCREEN:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    pygame.display.set_caption("3DRenderer with Z-Buffer")

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

    # ===== НОВЫЕ ПЕРЕМЕННЫЕ =====
    # Список объектов для демонстрации Z-буфера
    scene_objects = []
    main_object: Optional[Object] = objects[current_object].create()
    scene_objects.append(main_object)

    # Флаг использования Z-буфера
    use_zbuffer = True

    # Режим работы: single (один объект) или multiple (несколько объектов)
    scene_mode = "single"  # "single" или "multiple"

    # Настройки отображения
    show_faces = True  # Показывать грани (заливку)
    show_wireframe = True  # Показывать каркас (рёбра)
    show_normals = False  # Показывать векторы нормалей
    # ==============================

    rendered_object = render_object(main_object, renders[current_render], window_info, use_zbuffer)

    last_object = -1
    last_render = -1

    input_boxes = {
        "translation_x": "0",
        "translation_y": "20",
        "translation_z": "0",
        "scale_x": "1.1",
        "scale_y": "1.1",
        "scale_z": "1.1",
        "rotation_angle": "15",
        "custom_line_p1": "0,0,0",
        "custom_line_p2": "100,100,100",
        "custom_rotation_angle": "30",
        "filename": "model",
        "plot_function": "math.sin(x) * math.cos(y) * 2",
        "plot_x_min": "-6",
        "plot_x_max": "6",
        "plot_y_min": "-6",
        "plot_y_max": "6",
        "plot_n_points": "40",
        "rot_shape_profile": "(50, 0) (80, 50) (80, 100) (50, 150)",
        "rot_shape_iterations": "16",
    }

    active_input = None

    y_offset = 80
    btn_width, btn_height = 200, 35

    plot_block_height = 40 + 35 * 4 + 40
    rot_shape_y_offset = y_offset + plot_block_height + 140

    transform_buttons = [
        Rectangle(1140, y_offset, btn_width, btn_height),  # Перенос
        Rectangle(1140, y_offset + 45, btn_width, btn_height),  # Масштаб
        Rectangle(1140, y_offset + 90, btn_width, btn_height),  # Поворот X
        Rectangle(1140, y_offset + 135, btn_width, btn_height),  # Поворот Y
        Rectangle(1140, y_offset + 180, btn_width, btn_height),  # Поворот Z
        Rectangle(1140, y_offset + 225, btn_width, btn_height),  # Отражение XY
        Rectangle(1140, y_offset + 270, btn_width, btn_height),  # Отражение XZ
        Rectangle(1140, y_offset + 315, btn_width, btn_height),  # Отражение YZ
        Rectangle(1140, y_offset + 360, btn_width, btn_height),  # Поворот вокруг произвольной прямой
        Rectangle(1140, y_offset + 405, btn_width, btn_height),  # Сброс
    ]

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
        "custom_rotation_angle": Rectangle(800, y_offset + 430, 170, 30),
        "filename": Rectangle(20, window_info.height - 185, 150, 35),
        "plot_function": Rectangle(100, y_offset + 100, 350, 35),
        "plot_x_min": Rectangle(110, y_offset + 145, 80, 35),
        "plot_x_max": Rectangle(200, y_offset + 145, 80, 35),
        "plot_y_min": Rectangle(110, y_offset + 190, 80, 35),
        "plot_y_max": Rectangle(200, y_offset + 190, 80, 35),
        "plot_n_points": Rectangle(170, y_offset + 235, 110, 35),
        "rot_shape_profile": Rectangle(20, rot_shape_y_offset + 40, 430, 35),
        "rot_shape_iterations": Rectangle(150, rot_shape_y_offset + 85, 80, 35),
    }

    file_buttons = [
        Rectangle(20, window_info.height - 150, 150, 35),  # Загрузить
        Rectangle(20, window_info.height - 105, 150, 35),  # Сохранить
    ]

    plot_button = Rectangle(20, y_offset + 280, 430, 40)
    rot_shape_button = Rectangle(20, rot_shape_y_offset + 130, 430, 40)

    auto_rotate = True
    auto_rotate_button = Rectangle(470, 20, 200, 35)

    # ===== НОВЫЕ КНОПКИ =====
    zbuffer_toggle_button = Rectangle(690, 20, 200, 35)
    scene_mode_button = Rectangle(910, 20, 200, 35)
    add_object_button = Rectangle(1130, 20, 120, 35)
    clear_scene_button = Rectangle(1260, 20, 120, 35)

    # Кнопки режимов отображения (второй ряд)
    faces_toggle_button = Rectangle(20, 65, 150, 35)
    wireframe_toggle_button = Rectangle(180, 65, 150, 35)
    normals_toggle_button = Rectangle(340, 65, 180, 35)
    # ========================

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
                        input_boxes[active_input] += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    button_clicked = True
                    active_input = None
                    for key, rect in input_rects.items():
                        if (rect.x <= event.pos[0] <= rect.x + rect.width and
                            rect.y <= event.pos[1] <= rect.y + rect.height):
                            active_input = key
                            break

        # Автоматическое вращение
        if auto_rotate:
            if scene_mode == "single" and main_object:
                rotate_around_center(main_object, 'Y', np.radians(0.7))
                rotate_around_center(main_object, 'X', np.radians(0.4))
            elif scene_mode == "multiple":
                for obj in scene_objects:
                    rotate_around_center(obj, 'Y', np.radians(0.7))
                    rotate_around_center(obj, 'X', np.radians(0.4))

        camera.update()
        screen.fill(ui_background_color)

        # Рендеринг сцены
        if scene_mode == "single":
            rendered_object = render_object(main_object, renders[current_render], window_info, use_zbuffer)
            if rendered_object:
                for rp in rendered_object:
                    rp.draw(screen, show_faces, show_wireframe)
                    if show_normals:
                        normal_color = getattr(config, 'NORMAL_COLOR', (255, 0, 0))
                        rp.draw_normal(screen, normal_color)
        else:  # multiple mode
            rendered_polygons = render_multiple_objects(scene_objects, renders[current_render], window_info, use_zbuffer)
            if rendered_polygons:
                for rp in rendered_polygons:
                    rp.draw(screen, show_faces, show_wireframe)
                    if show_normals:
                        normal_color = getattr(config, 'NORMAL_COLOR', (255, 0, 0))
                        rp.draw_normal(screen, normal_color)

        # ===== UI ЭЛЕМЕНТЫ =====

        # ===== КНОПКИ РЕЖИМОВ ОТОБРАЖЕНИЯ (второй ряд) =====

        # Кнопка отображения граней
        faces_text = "Грани: ВКЛ" if show_faces else "Грани: ВЫКЛ"
        if button(screen, small_font, faces_toggle_button, faces_text) and button_clicked:
            show_faces = not show_faces
            button_clicked = False

        # Кнопка отображения каркаса
        wireframe_text = "Каркас: ВКЛ" if show_wireframe else "Каркас: ВЫКЛ"
        if button(screen, small_font, wireframe_toggle_button, wireframe_text) and button_clicked:
            show_wireframe = not show_wireframe
            button_clicked = False

        # Кнопка отображения нормалей
        normals_text = "Нормали: ВКЛ" if show_normals else "Нормали: ВЫКЛ"
        if button(screen, small_font, normals_toggle_button, normals_text) and button_clicked:
            show_normals = not show_normals
            button_clicked = False

        # ===================================================

        # Кнопка вращения
        rotate_btn_text = "Вращение: ВКЛ" if auto_rotate else "Вращение: ВЫКЛ"
        if button(screen, font, auto_rotate_button, rotate_btn_text) and button_clicked:
            auto_rotate = not auto_rotate
            button_clicked = False

        # ===== НОВЫЕ КНОПКИ UI =====

        # Кнопка переключения Z-буфера
        zbuffer_text = "Z-Buffer: ВКЛ" if use_zbuffer else "Z-Buffer: ВЫКЛ"
        if button(screen, font, zbuffer_toggle_button, zbuffer_text) and button_clicked:
            use_zbuffer = not use_zbuffer
            button_clicked = False

        # Кнопка режима сцены
        mode_text = "Режим: ОДИН" if scene_mode == "single" else "Режим: МНОГО"
        if button(screen, font, scene_mode_button, mode_text) and button_clicked:
            if scene_mode == "single":
                scene_mode = "multiple"
                # Создаем демонстрационную сцену с несколькими объектами
                scene_objects = []

                # Центральный объект
                obj1 = create_icosahedron()
                scene_objects.append(obj1)

                # Объект слева
                obj2 = create_cube()
                obj2.apply_transformation(translation_matrix(-250, 0, 0))
                obj2.apply_transformation(scale_matrix(0.7, 0.7, 0.7))
                scene_objects.append(obj2)

                # Объект справа
                obj3 = create_octahedron()
                obj3.apply_transformation(translation_matrix(250, 0, 0))
                obj3.apply_transformation(scale_matrix(0.8, 0.8, 0.8))
                scene_objects.append(obj3)

                # Объект сзади (больше по Z)
                obj4 = create_tetrahedron()
                obj4.apply_transformation(translation_matrix(0, 150, -200))
                obj4.apply_transformation(scale_matrix(1.2, 1.2, 1.2))
                scene_objects.append(obj4)

            else:
                scene_mode = "single"
                scene_objects = [main_object]
            button_clicked = False

        # Кнопка добавления объекта
        if button(screen, small_font, add_object_button, "Добавить") and button_clicked:
            if scene_mode == "multiple":
                new_obj = objects[current_object].create()
                # Случайное смещение для нового объекта
                import random
                dx = random.randint(-300, 300)
                dy = random.randint(-200, 200)
                dz = random.randint(-200, 200)
                new_obj.apply_transformation(translation_matrix(dx, dy, dz))
                scene_objects.append(new_obj)
            button_clicked = False

        # Кнопка очистки сцены
        if button(screen, small_font, clear_scene_button, "Очистить") and button_clicked:
            if scene_mode == "multiple":
                scene_objects = []
            button_clicked = False

        # ===========================

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
            if scene_mode == "single":
                scene_objects = [main_object]
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
            last_render = current_render

        # Отображение информации
        info_y_offset = 110  # Смещаем информацию ниже, чтобы не перекрывать кнопки
        if scene_mode == "single":
            center = main_object.get_center()
            center_text = small_font.render(f"Центр: {center}", True, (0, 0, 0))
            screen.blit(center_text, (20, info_y_offset))
        else:
            objects_text = small_font.render(f"Объектов в сцене: {len(scene_objects)}", True, (0, 0, 0))
            screen.blit(objects_text, (20, info_y_offset))

        # --- РАЗДЕЛ ПОСТРОЕНИЯ ГРАФИКА ---
        plot_title_text = font.render("Построение графика z = f(x, y)", True, (0, 0, 0))
        screen.blit(plot_title_text, (20, y_offset + 70))
        screen.blit(small_font.render("f(x, y) =", True, (0, 0, 0)), (20, y_offset + 110))
        screen.blit(small_font.render("X min, max:", True, (0, 0, 0)), (20, y_offset + 152))
        screen.blit(small_font.render("Y min, max:", True, (0, 0, 0)), (20, y_offset + 197))
        screen.blit(small_font.render("Кол-во точек:", True, (0, 0, 0)), (20, y_offset + 242))

        if button(screen, font, plot_button, "Построить график") and button_clicked:
            try:
                func_str = input_boxes["plot_function"]
                x_min = float(input_boxes["plot_x_min"])
                x_max = float(input_boxes["plot_x_max"])
                y_min = float(input_boxes["plot_y_min"])
                y_max = float(input_boxes["plot_y_max"])
                n_points = int(input_boxes["plot_n_points"])
                func = lambda x, y: eval(func_str, {"x": x, "y": y, "math": math})
                plot_obj = Plot(
                    f=func,
                    cut_off=((x_min, x_max), (y_min, y_max)),
                    number_of_points=n_points
                )
                temp_plot_filename = os.path.join(models_dir, "_temp_plot.obj")
                plot_obj.export(temp_plot_filename)
                main_object = load_obj(temp_plot_filename)
                if scene_mode == "single":
                    scene_objects = [main_object]
            except Exception as e:
                print(f"Ошибка при построении графика: {e}")
            button_clicked = False

        # --- РАЗДЕЛ ПОСТРОЕНИЯ ФИГУРЫ ВРАЩЕНИЯ ---
        rot_shape_title_text = font.render("Построение фигуры вращения", True, (0, 0, 0))
        screen.blit(rot_shape_title_text, (20, rot_shape_y_offset))
        screen.blit(small_font.render("Профиль (x, y) - список точек:", True, (0, 0, 0)), (20, rot_shape_y_offset + 15))
        screen.blit(small_font.render("Итерации/Сегменты:", True, (0, 0, 0)), (20, rot_shape_y_offset + 92))

        if button(screen, font, rot_shape_button, "Построить фигуру вращения") and button_clicked:
            try:
                profile_str = input_boxes["rot_shape_profile"]
                iterations = int(input_boxes["rot_shape_iterations"])
                dots = get_dots_from_string(profile_str)
                rot_shape_object = create_solid_of_revolution(dots, iterations)
                main_object = rot_shape_object
                if scene_mode == "single":
                    scene_objects = [main_object]
            except Exception as e:
                print(f"Ошибка при построении фигуры вращения: {e}")
            button_clicked = False

        # --- Поля ввода и кнопки преобразований ---
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

        for key, rect in input_rects.items():
            input_box(screen, small_font, rect, input_boxes[key], active_input == key)

        # Применяем преобразования к активному объекту (или ко всем в режиме multiple)
        target_objects = scene_objects if scene_mode == "multiple" else [main_object]

        if button(screen, font, transform_buttons[0], "Перенос") and button_clicked:
            try:
                dx = float(input_boxes["translation_x"])
                dy = float(input_boxes["translation_y"])
                dz = float(input_boxes["translation_z"])
                for obj in target_objects:
                    obj.apply_transformation(translation_matrix(dx, dy, dz))
            except ValueError:
                pass
            button_clicked = False

        if button(screen, font, transform_buttons[1], "Масштаб") and button_clicked:
            try:
                sx = float(input_boxes["scale_x"])
                sy = float(input_boxes["scale_y"])
                sz = float(input_boxes["scale_z"])
                for obj in target_objects:
                    scale_relative_to_center(obj, sx, sy, sz)
            except ValueError:
                pass
            button_clicked = False

        if button(screen, font, transform_buttons[2], "Поворот X") and button_clicked:
            try:
                angle = np.radians(float(input_boxes["rotation_angle"]))
                for obj in target_objects:
                    rotate_around_center(obj, 'X', angle)
            except ValueError:
                pass
            button_clicked = False

        if button(screen, font, transform_buttons[3], "Поворот Y") and button_clicked:
            try:
                angle = np.radians(float(input_boxes["rotation_angle"]))
                for obj in target_objects:
                    rotate_around_center(obj, 'Y', angle)
            except ValueError:
                pass
            button_clicked = False

        if button(screen, font, transform_buttons[4], "Поворот Z") and button_clicked:
            try:
                angle = np.radians(float(input_boxes["rotation_angle"]))
                for obj in target_objects:
                    rotate_around_center(obj, 'Z', angle)
            except ValueError:
                pass
            button_clicked = False

        if button(screen, font, transform_buttons[5], "Отражение XY") and button_clicked:
            for obj in target_objects:
                obj.apply_transformation(reflection_xy_matrix())
            button_clicked = False

        if button(screen, font, transform_buttons[6], "Отражение XZ") and button_clicked:
            for obj in target_objects:
                obj.apply_transformation(reflection_xz_matrix())
            button_clicked = False

        if button(screen, font, transform_buttons[7], "Отражение YZ") and button_clicked:
            for obj in target_objects:
                obj.apply_transformation(reflection_yz_matrix())
            button_clicked = False

        if button(screen, font, transform_buttons[8], "Поворот вокруг прямой") and button_clicked:
            try:
                p1_coords = [float(x.strip()) for x in input_boxes["custom_line_p1"].split(',')]
                p2_coords = [float(x.strip()) for x in input_boxes["custom_line_p2"].split(',')]
                angle = np.radians(float(input_boxes["custom_rotation_angle"]))

                if len(p1_coords) == 3 and len(p2_coords) == 3:
                    p1 = Point(p1_coords[0], p1_coords[1], p1_coords[2])
                    p2 = Point(p2_coords[0], p2_coords[1], p2_coords[2])
                    for obj in target_objects:
                        rotate_around_line(obj, p1, p2, angle)
            except ValueError:
                pass
            button_clicked = False

        if button(screen, font, transform_buttons[9], "Сброс") and button_clicked:
            main_object = objects[current_object].create()
            if scene_mode == "single":
                scene_objects = [main_object]
            button_clicked = False

        # Кнопки файловых операций
        if button(screen, font, file_buttons[0], "Загрузить OBJ") and button_clicked:
            filename = input_boxes["filename"] + '.obj'
            file_path = os.path.join(models_dir, filename)
            try:
                main_object = load_obj(file_path)
                if scene_mode == "single":
                    scene_objects = [main_object]
                print(f"Файл {filename} загружен.")
            except:
                print(f"Не удалось загрузить файл {filename}")
            button_clicked = False

        if button(screen, font, file_buttons[1], "Сохранить OBJ") and button_clicked:
            filename = f"saved_model_{datetime.now().strftime('%H_%M_%S')}.obj"
            file_path = os.path.join(models_dir, filename)
            try:
                save_obj(main_object, file_path)
            except Exception as e:
                print(f"Ошибка сохранения: {e}")
            button_clicked = False

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    app()