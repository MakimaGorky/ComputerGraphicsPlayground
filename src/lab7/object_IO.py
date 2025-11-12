from primitives import *


def save_obj(obj: Object, filename: str):
    """
    Сохранение модели в формате Wavefront OBJ.
    Производит преобразование из внутренней системы координат в стандартную для OBJ (инверсия оси Y).
    """
    with open(filename, 'w') as f:
        f.write("# Wavefront OBJ file\n")
        f.write("# Created by 3DRenderer\n\n")

        # Собираем все уникальные вершины, чтобы избежать дублирования
        vertices = []
        vertex_map = {}

        for poly in obj.polygons:
            for v in poly.vertices:
                # Ключ для словаря создается из округленных координат для устранения
                # неточностей с плавающей запятой и объединения близких вершин.
                key = (round(v.x, 6), round(v.y, 6), round(v.z, 6))
                if key not in vertex_map:
                    vertex_map[key] = len(vertices) + 1  # Индексы в OBJ начинаются с 1
                    vertices.append(v)

        # Записываем вершины в файл
        # При записи инвертируем ось Y для совместимости со стандартом OBJ (Y-up)
        for v in vertices:
            f.write(f"v {v.x} {-v.y} {v.z}\n")

        f.write("\n")

        # Записываем грани (полигоны)
        for poly in obj.polygons:
            face_indices = []
            for v in poly.vertices:
                key = (round(v.x, 6), round(v.y, 6), round(v.z, 6))
                face_indices.append(str(vertex_map[key]))
            f.write(f"f {' '.join(face_indices)}\n")

    print(f"Модель сохранена в файл: {filename}")


def load_obj(filename: str) -> Object:
    print(filename)

    """
    Загрузка модели из формата Wavefront OBJ.
    Производит преобразование из системы координат OBJ во внутреннюю (инверсия оси Y).
    """
    vertices = []
    faces = []

    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                parts = line.split()
                if not parts:
                    continue

                if parts[0] == 'v':
                    # Вершина
                    # Упрощен парсинг: убрана ненужная лямбда-функция
                    x, y, z = map(float, parts[1:4])
                    # Инвертируем ось Y для преобразования в нашу систему координат
                    vertices.append(Point(x, -y, z))

                elif parts[0] == 'f':
                    # Грань
                    face_indices = []
                    for part in parts[1:]:
                        # Обрабатываем формат 'v/vt/vn' или 'v//vn', беря только индекс вершины
                        idx_str = part.split('/')[0]
                        face_indices.append(int(idx_str) - 1)  # OBJ индексы начинаются с 1
                    faces.append(face_indices)

        # Создаем объект из загруженных данных
        obj = Object()
        for face in faces:
            # Проверяем, что индексы не выходят за пределы списка вершин
            if all(i < len(vertices) for i in face):
                poly = Polygon([vertices[i] for i in face])
                obj.add_face(poly)
            else:
                print(f"Предупреждение: некорректный индекс грани в файле {filename}. Грань пропущена.")

        print(f"Модель загружена из файла: {filename}")
        print(f"Вершин: {len(vertices)}, Граней: {len(faces)}")
        return obj

    except FileNotFoundError:
        print(f"Ошибка: файл не найден по пути: {filename}")
        return create_cube()  # Возвращаем куб по умолчанию
    except (ValueError, IndexError) as e:
        print(f"Ошибка парсинга файла '{filename}': {e}")
        return create_cube()  # Возвращаем куб по умолчанию
    except Exception as e:
        print(f"Произошла непредвиденная ошибка при загрузке файла: {e}")
        return create_cube() # Возвращаем куб по умолчанию