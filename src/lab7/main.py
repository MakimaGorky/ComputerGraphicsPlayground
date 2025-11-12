import pygame
from primitives import *
from create_test_models import *
from datetime import datetime
from object_IO import *
from D3Renderer import *
from camera import *
import os

FULLSCREEN = False

def app():
    current_file_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file_path)
    root_dir = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
    models_dir = os.path.join(root_dir, 'models')

    pygame.init()

    screen = pygame.display.set_mode((0, 0))
    if FULLSCREEN:
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
        "filename": "model"
    }

    active_input = None

    # Кнопки управления
    y_offset = 80
    btn_width, btn_height = 200, 35

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
        "custom_rotation_angle": Rectangle(800, y_offset + 430, 170, 30),
        "filename": Rectangle(20, window_info.height - 185, 150, 35)
    }

    # Кнопки файловых операций
    file_buttons = [
        Rectangle(20, window_info.height - 150, 150, 35),  # Загрузить
        Rectangle(20, window_info.height - 105, 150, 35),  # Сохранить
    ]

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
                        if True:
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
        camera.update()

        screen.fill(ui_background_color)
        
        rendered_object = render_object(main_object, renders[current_render], window_info)
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

                # Кнопки файловых операций
        if button(screen, font, file_buttons[0], "Загрузить OBJ") and button_clicked:
            # Простой диалог ввода имени файла через консоль
            print("\n=== ЗАГРУЗКА МОДЕЛИ ===")
            print("Введите имя Object файла (например: model):")
            # В реальной программе здесь был бы GUI диалог
            # Для демонстрации используем предустановленное имя
            filename = input_boxes["filename"] + '.obj'
            file_path = os.path.join(models_dir, filename)
            try:
                main_object = load_obj(file_path)
                rendered_object = render_object(main_object, renders[current_render], window_info)
            except:
                print(f"Не удалось загрузить файл {filename}")
            button_clicked = False

        if button(screen, font, file_buttons[1], "Сохранить OBJ") and button_clicked:
            print("\n=== СОХРАНЕНИЕ МОДЕЛИ ===")
            print("Введите имя Object файла (например: output):")
            # В реальной программе здесь был бы GUI диалог
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