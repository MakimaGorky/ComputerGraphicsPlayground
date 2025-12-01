import pygame
import numpy as np
import math
from light import *

# --- Настройки рендеринга Pygame ---

def project_3d_to_2d(point_3d, width, height, projection_distance=5):
    """
    Простейшая перспективная проекция (или ортогональная, если distance очень велико).
    z=0 считается плоскостью экрана.
    """
    x, y, z = point_3d
    
    # Перспективное деление (для z < 0, z становится 'расстоянием')
    # Мы ожидаем, что объект находится "за" плоскостью камеры (в нашем случае Z < D)
    # Используем простую проекцию: x_screen = x * f / z
    # В нашем случае, камера смотрит вдоль оси Z
    
    # Для демонстрации используем простейшую ортогональную проекцию с масштабом,
    # так как аффинные преобразования уже применены к объекту.
    # Фактическое преобразование камеры/проекции - это отдельный шаг в конвейере.
    
    # Проекция на плоскость (X, Y) с учетом Z для масштаба
    # Смещаем центр в (width/2, height/2)
    scale = projection_distance / (projection_distance - z)
    x_2d = int(x * 100 * scale + width / 2)
    y_2d = int(y * 100 * scale + height / 2)
    
    return (x_2d, y_2d)

# --- Основной цикл Pygame ---

def run_gui():
    pygame.init()

    # Параметры окна
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("3D Lighting and Shading (Phong Model)")
    clock = pygame.time.Clock()

    # Создание источника света и объекта
    light = LightSource(position=(5, 5, -10), color=(0.8, 0.8, 0.8))

    cube_vertices = [
        (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
        (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)
    ]
    cube_faces = [
        (0, 1, 2), (2, 3, 0), # Front
        (4, 5, 6), (6, 7, 4), # Back
        (1, 5, 6), (6, 2, 1), # Right
        (4, 0, 3), (3, 7, 4), # Left
        (3, 2, 6), (6, 7, 3), # Top
        (4, 5, 1), (1, 0, 4)  # Bottom
    ]
    
    cube = Object3D(
        vertices=cube_vertices, 
        faces=cube_faces, 
        color=(0.1, 0.5, 0.9), 
        shininess=200.0        
    )

    # Позиция наблюдателя (камеры) в мировых координатах
    VIEW_POSITION = np.array([0, 0, -10]) # Камера находится на Z=-10 и смотрит на объект у Z=0

    angle = 0 # Угол для вращения

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Обновление: Вращение объекта (Аффинное преобразование) ---
        angle += 1 # Увеличиваем угол
        cube.transform_matrix = np.identity(4) # Сбрасываем матрицу, чтобы избежать постоянного накопления
        
        # 1. Поворот
        rotation_matrix = create_rotation_y_matrix(angle)
        cube.apply_transform(rotation_matrix)
        
        # 2. Перенос (Размещение объекта в пространстве, чтобы он был виден)
        translation_matrix = create_translation_matrix(0, 0, 5) # Смещаем объект, чтобы он был перед камерой (Z=5)
        cube.apply_transform(translation_matrix)

        # --- Рендеринг ---
        screen.fill((10, 10, 30)) # Темный фон

        transformed_vertices = cube.get_transformed_vertices()
        
        # 1. Сортировка граней по Z (для простейшего алгоритма "художника")
        # Сортируем грани, чтобы рендерить их от самой дальней к самой ближней
        render_order = []
        for i in range(len(cube.faces)):
            face_indices = cube.faces[i]
            # Берем Z-координату центра грани
            face_center_z = np.mean([transformed_vertices[idx][2] for idx in face_indices])
            render_order.append((face_center_z, i))
        
        # Сортируем по Z (от меньшего Z (дальше) к большему Z (ближе))
        render_order.sort(key=lambda item: item[0], reverse=True) 

        # 2. Отрисовка
        for z, face_index in render_order:
            # Расчет цвета с учетом освещения и отсечения
            color_255 = cube.get_shading_for_face(face_index, light, VIEW_POSITION)
            
            if color_255 is not None:
                # Грань видима и освещена
                v_indices = cube.faces[face_index]
                
                # Преобразование 3D-точек грани в 2D-координаты экрана
                points_2d = [
                    project_3d_to_2d(transformed_vertices[idx], WIDTH, HEIGHT) 
                    for idx in v_indices
                ]
                
                # Отрисовка полигона (грани)
                pygame.draw.polygon(screen, color_255, points_2d, 0) # 0 = заливка
                # Небольшой контур для наглядности
                pygame.draw.polygon(screen, (50, 50, 50), points_2d, 1)

        # Обновление экрана
        pygame.display.flip()
        
        # Ограничение FPS
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    run_gui()
