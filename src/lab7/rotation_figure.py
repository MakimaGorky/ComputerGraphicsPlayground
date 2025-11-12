from primitives import *
from transformations import *

def create_rotation_figure(profile_points: List[Point], axis: str, divisions: int) -> Object:
    """
    Создание фигуры вращения
    profile_points: точки образующей
    axis: ось вращения ('X', 'Y' или 'Z')
    divisions: количество разбиений
    """
    if len(profile_points) < 2:
        return Object()

    angle_step = 2 * np.pi / divisions
    obj = Object()

    # Создаем вершины для каждого угла поворота
    rotated_profiles = []
    for i in range(divisions):
        angle = i * angle_step
        rotated_profile = []

        for p in profile_points:
            # Создаем копию точки
            new_point = Point(p.x, p.y, p.z)

            # Применяем поворот вокруг выбранной оси
            if axis == 'X':
                matrix = rotation_x_matrix(angle)
            elif axis == 'Y':
                matrix = rotation_y_matrix(angle)
            else:  # Z
                matrix = rotation_z_matrix(angle)

            h = new_point.to_homogeneous()
            transformed = np.dot(matrix, h)
            new_point.from_homogeneous(transformed)
            rotated_profile.append(new_point)

        rotated_profiles.append(rotated_profile)

    # Создаем грани между соседними профилями
    for i in range(divisions):
        next_i = (i + 1) % divisions

        for j in range(len(profile_points) - 1):
            # Четырехугольная грань между двумя профилями
            p1 = rotated_profiles[i][j]
            p2 = rotated_profiles[next_i][j]
            p3 = rotated_profiles[next_i][j + 1]
            p4 = rotated_profiles[i][j + 1]

            obj.add_face(Polygon([p1, p2, p3, p4]))

    return obj