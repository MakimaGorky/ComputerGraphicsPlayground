from primitives import Point, Polygon, Object
import config


def load_obj(filename: str) -> Object:
    """
    Загружает 3D-модель из файла формата .obj.

    Args:
        filename: Путь к .obj файлу.

    Returns:
        Объект типа Object, представляющий модель.
    """
    vertices = []
    uv_coords = []
    polygons = []

    # Используем константу масштабирования из файла конфигурации для приведения модели к общему размеру
    scale = config.OBJ_SCALE

    has_uv_coordinats = False

    try:
        with open(filename, 'r') as f:
            for line in f:
                if line.startswith('v '):
                    # Парсинг координат вершины
                    parts = line.strip().split()
                    # .obj файлы могут содержать 4-й компонент (w), мы его игнорируем
                    x, y, z = map(float, parts[1:4])
                    # Масштабируем вершину при загрузке
                    vertices.append(Point(x * scale, -y * scale, z * scale))
                elif line.startswith('vt '):
                    if not has_uv_coordinats:
                        has_uv_coordinats = True
                    parts = line.strip().split()
                    u, v = map(float, parts[1:3])
                    uv_coords.append([u, v])
                elif line.startswith('f '):
                    # Парсинг индексов вершин для полигона (грани)
                    parts = line.strip().split()[1:]
                    face_indices = []
                    face_uv_indices = []
                    for part in parts:
                        # Индексы в .obj могут быть сложными (v/vt/vn), извлекаем только индекс вершины
                        index_str, uv_index_str = part.split('/')[0:2]
                        # Индексы в .obj начинаются с 1, а в нашем списке - с 0
                        face_indices.append(int(index_str) - 1)
                        face_uv_indices.append(int(uv_index_str) - 1)

                    # Создаем полигон из вершин по их индексам
                    polygon_vertices = [vertices[i] for i in face_indices]
                    for i in range(len(face_uv_indices)):
                        polygon_vertices[i].u = uv_coords[face_uv_indices[i]][0]
                        polygon_vertices[i].v = uv_coords[face_uv_indices[i]][1]
                    polygons.append(Polygon(polygon_vertices))

    except FileNotFoundError:
        print(f"Ошибка: Файл не найден по пути {filename}")
        return Object()  # Возвращаем пустой объект в случае ошибки
    except Exception as e:
        print(f"Ошибка при чтении файла {filename}: {e}")
        return Object()

    print(f"Модель {filename} успешно загружена.")
    return Object(polygons, has_uv_coordinats)


def save_obj(obj: Object, filename: str):
    """
    Сохраняет 3D-модель в файл формата .obj.

    Args:
        obj: Объект типа Object для сохранения.
        filename: Имя файла для сохранения.
    """
    # Получаем коэффициент масштабирования из конфига для выполнения обратного преобразования
    scale = config.OBJ_SCALE
    # Предотвращение деления на ноль, если масштаб вдруг окажется нулевым
    if scale == 0:
        scale = 1.0

    all_vertices = []
    # Собираем все вершины из всех полигонов объекта
    for poly in obj.polygons:
        all_vertices.extend(poly.vertices)

    # Создаем словарь для отслеживания уникальных вершин и их индексов
    # Ключ - кортеж координат, значение - 1-основанный индекс
    vertex_to_index = {}
    unique_vertices = []

    for vertex in all_vertices:
        # Округляем значения для корректного сравнения float-чисел
        v_tuple = (round(vertex.x, 6), -round(vertex.y, 6), round(vertex.z, 6))
        if v_tuple not in vertex_to_index:
            unique_vertices.append(vertex)
            # .obj использует 1-основанную индексацию
            vertex_to_index[v_tuple] = len(unique_vertices)

    try:
        with open(filename, 'w') as f:
            f.write("# Model saved from 3DRenderer\n")

            # Записываем все уникальные вершины с применением АНТИ-масштабирования
            for v in unique_vertices:
                # Делим координаты на тот же коэффициент, на который умножали при загрузке
                f.write(f"v {v.x / scale} {v.y / scale} {v.z / scale}\n")

            f.write("\n")

            # Записываем информацию о гранях (полигонах)
            for poly in obj.polygons:
                f.write("f")
                for vertex in poly.vertices:
                    v_tuple = (round(vertex.x, 6), round(-vertex.y, 6), round(vertex.z, 6))
                    index = vertex_to_index[v_tuple]
                    f.write(f" {index}")
                f.write("\n")

        print(f"Модель успешно сохранена в файл {filename}")

    except Exception as e:
        print(f"Ошибка при сохранении файла {filename}: {e}")