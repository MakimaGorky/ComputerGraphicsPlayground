import numpy as np
import math
from primitives import * # Assume primitives.py provides Point, Polygon, Object, etc.
import config
from typing import List, Tuple, Any, Optional
import os # Добавим os для from_obj

# --- Вспомогательные функции для матриц (для полноты) ---

def create_rotation_y_matrix(degree):
    angle = math.radians(degree)
    c = np.cos(angle)
    s = np.sin(angle)
    return np.array([
        [c, 0, s, 0],
        [0, 1, 0, 0],
        [-s, 0, c, 0],
        [0, 0, 0, 1]
    ])


class LightSource:
    def __init__(self, position, color=(1.0, 1.0, 1.0)):
        self.position = np.array(position, dtype=float)
        self.color = np.array(color, dtype=float)

single_light_source = LightSource((300, 300, 300), color=(1, 0, 0))

class LitObject(Object):
    def __init__(self, polygons: List[Polygon], color=(0.7, 0.7, 0.7), ambient_color=(0.1, 0.1, 0.1), shininess=100.0):
        super().__init__(polygons) 
        
        self.polygons = polygons
        
        # Фонг момент
        self.color_diffuse = np.array(color, dtype=float)
        self.color_specular = np.array((1.0, 1.0, 1.0), dtype=float)
        self.color_ambient = np.array(ambient_color, dtype=float)
        self.shininess = shininess

        # Матрица аффинного преобразования (единичная)
        # TODO: реализовать преобразования
        self.transform_matrix = np.identity(4)
        
        self.calculate_normals()

    # --- Вспомогательные методы для работы с primitives.Point и numpy ---
    
    def _point_to_nparray(self, p: Point) -> np.ndarray:
        """Конвертирует primitives.Point в 3D numpy array."""
        return np.array([p.x, p.y, p.z], dtype=float)
    
    def _nparray_to_point(self, n: np.ndarray) -> Point:
        """Конвертирует 3D numpy array в primitives.Point."""
        return Point(n[0], n[1], n[2])

    def _transform_point(self, point: Point) -> np.ndarray:
        """ Преобразует Point в гомогенных координатах и возвращает декартовы np.ndarray """
        point_homogeneous = point.to_homogeneous() # Предполагается, что Point имеет метод to_homogeneous
        transformed_point = np.dot(self.transform_matrix, point_homogeneous)
        # Возвращаем декартовы координаты (делим на w)
        return transformed_point[:3] / transformed_point[3]

    def _transform_normal(self, normal: Point) -> np.ndarray:
        """ Преобразует нормаль (Point) и возвращает нормализованный np.ndarray """
        normal_vec = self._point_to_nparray(normal)
        M_3x3 = self.transform_matrix[:3, :3]
        transformed_normal = np.dot(M_3x3, normal_vec)
        norm_magnitude = np.linalg.norm(transformed_normal)
        # Нормализация
        return transformed_normal / norm_magnitude if norm_magnitude != 0 else np.zeros(3)

    # --- Методы освещения (переписанные) ---

    def calculate_face_normal(self, poly: Polygon) -> np.ndarray:
        """
        Вычисляет нормаль грани (полигона) с помощью векторного произведения.
        Сохраняет результат в poly.normal (в виде Point) и возвращает как numpy array.
        """
        if len(poly.vertices) < 3:
            poly.normal = None
            return np.zeros(3)

        # Берем первые три точки полигона
        v1 = self._point_to_nparray(poly.vertices[0])
        v2 = self._point_to_nparray(poly.vertices[1])
        v3 = self._point_to_nparray(poly.vertices[2])

        edge1 = v2 - v1
        edge2 = v3 - v1
        
        normal = np.cross(edge1, edge2)
        norm_magnitude = np.linalg.norm(normal)
        
        if norm_magnitude != 0:
            normalized_normal = normal / norm_magnitude
            poly.normal = self._nparray_to_point(normalized_normal)
            return normalized_normal
        else:
            poly.normal = Point(0, 0, 0)
            return np.zeros(3)


    def calculate_normals(self):
        """
        Нормали сохраняются в свойстве 'normal' каждого Polygon.
        """
        for poly in self.polygons:
            self.calculate_face_normal(poly)
        

    def back_face_culling(self, poly: Polygon, view_position: Tuple[float, float, float]) -> bool:
        """
        Реализует отсечение нелицевых граней.
        """
        if poly.normal is None:
            return True

        # 1. Берем преобразованную точку на поверхности (первая вершина)
        point_on_surface_np = self._transform_point(poly.vertices[0])
        
        # 2. Вектор от поверхности к наблюдателю (камере)
        view_position_np = np.array(view_position, dtype=float)
        V = view_position_np - point_on_surface_np
        V = V / np.linalg.norm(V)
        
        # 3. Преобразованная нормаль грани
        face_normal_np = self._transform_normal(poly.normal)
        
        # 4. Проверка скалярным произведением (N . V < 0 -> отсечь)
        dot_product = np.dot(face_normal_np, V)
        
        return dot_product < 0
        
        
    def phong_shading(self, point: np.ndarray, normal: np.ndarray, light_source: LightSource, view_position: np.ndarray) -> np.ndarray:
        """
        Расчет цвета в точке с использованием модели Фонга.
        Этот метод остается без изменений, так как он работает с np.ndarray.
        """
        N = normal
        
        # Вектор направления обзора (от точки к камере)
        V = view_position - point
        V = V / np.linalg.norm(V)

        # Вектор направления света (от точки к источнику)
        L = light_source.position - point
        L = L / np.linalg.norm(L)

        # 1. Фоновое (Ambient) освещение
        I_ambient = self.color_ambient * light_source.color

        # 2. Диффузное (Diffuse) освещение (модель Ламберта)
        N_dot_L = np.dot(N, L)
        diffuse_intensity = max(0.0, N_dot_L)
        I_diffuse = self.color_diffuse * light_source.color * diffuse_intensity

        # 3. Зеркальное (Specular) освещение (блики)
        R = 2 * N_dot_L * N - L
        R = R / np.linalg.norm(R)
        
        R_dot_V = np.dot(R, V)
        
        specular_intensity = max(0.0, R_dot_V)**self.shininess
        I_specular = self.color_specular * light_source.color * specular_intensity

        final_color = I_ambient + I_diffuse + I_specular
        return np.clip(final_color, 0.0, 1.0)
    
    
    def get_shading_for_face(self, poly: Polygon, light_source: LightSource, view_position: Tuple[float, float, float]) -> Optional[np.ndarray]:
        """
        Вычисляет цвет для грани (плоское затенение) на основе Polygon.
        """
        view_position_np = np.array(view_position, dtype=float)

        if self.back_face_culling(poly, view_position):
            return None # Грань невидима

        # 1. Точка на поверхности (центр грани)
        center_point_primitives = poly.get_center()
        center_point_np = self._transform_point(center_point_primitives)
        
        # 2. Преобразованная нормаль
        face_normal_np = self._transform_normal(poly.normal)

        # 3. Расчет цвета
        final_color = self.phong_shading(center_point_np, face_normal_np, light_source, view_position_np)
        
        return final_color

    # --- Метод загрузки OBJ (также адаптирован для LitObject) ---
    
    # ... (from_obj метод остается как в последнем предложении, т.к. он уже возвращает LitObject) ...
    @staticmethod
    def from_obj(filename, color=(0.7, 0.7, 0.7), position=(0,0,0), scale=1.0):
        # ... (КОД ИЗ ВАШЕГО СНИППЕТА, КОТОРЫЙ ПРАВИЛЬНО СОЗДАЕТ Polygon) ...
        # (Обеспечивает совместимость с LitObject(polygons))
        
        vertices = []
        polygons = []

        # Используем константу масштабирования из файла конфигурации для приведения модели к общему размеру
        # config.OBJ_SCALE должно быть доступно
        try:
             # Масштаб берем из config
            scale_factor = config.OBJ_SCALE 
        except NameError:
             # Если config.OBJ_SCALE не определено, используем значение по умолчанию из аргументов
            scale_factor = scale 


        try:
            with open(filename, 'r') as f:
                for line in f:
                    if line.startswith('v '):
                        parts = line.strip().split()
                        x, y, z = map(float, parts[1:4])
                        # Применяем масштаб и инверсию Y для соответствия load_obj
                        vertices.append(Point(x * scale_factor + position[0], -y * scale_factor + position[1], z * scale_factor + position[2]))
                    elif line.startswith('f '):
                        parts = line.strip().split()[1:]
                        face_indices = []
                        for part in parts:
                            index_str = part.split('/')[0]
                            face_indices.append(int(index_str) - 1)

                        polygon_vertices = [vertices[i] for i in face_indices]
                        polygons.append(Polygon(polygon_vertices))

        except FileNotFoundError:
            print(f"Ошибка: Файл не найден по пути {filename}")
            return LitObject([]) 
        except Exception as e:
            print(f"Ошибка при чтении файла {filename}: {e}")
            return LitObject([])

        print(f"Модель {filename} успешно загружена.")
        return LitObject(polygons, color=color)

# main.py (Вставить после основных импортов)

def project_vertex(v: np.ndarray, width: int, height: int) -> Tuple[int, int]:
    """Простая перспективная проекция 3D точки (np.ndarray) на 2D экран."""
    x, y, z = v
    fov = 600  # "Фокусное расстояние"
    
    # Сдвиг Z, чтобы объект был перед камерой (для предотвращения деления на ноль)
    # Если координата Z объекта становится слишком большой, используем фиксированную удаленность
    dist_z = 1000 
    
    # Фактор масштабирования (пропорционально глубине)
    # Используем dist_z - z, чтобы при Z=0 фактор был максимальным, при Z=dist_z -> минимальным
    if (dist_z - z) > 0:
        factor = fov / (dist_z - z)
    else:
        # Если точка слишком далеко (за камерой), устанавливаем фактор, предотвращающий ошибки
        factor = 0.001 
    
    x_2d = x * factor + width / 2
    # Инвертируем Y, так как в Pygame Y растет вниз
    y_2d = -y * factor + height / 2 
    
    return int(x_2d), int(y_2d)


def render_lit_object(screen: pygame.Surface, obj: LitObject, light_source: LightSource, camera_pos: Tuple[float, float, float]):
    """
    Рисует объект LitObject с применением освещения Фонга.
    """
    width, height = screen.get_size()
    
    # 1. Сбор и расчет цвета для всех видимых граней
    faces_to_draw = []
    
    for poly in obj.polygons:
        # poly.normal был рассчитан в obj.calculate_normals() при инициализации
        
        # Вычисляем цвет грани (включает culling, трансформацию и shading)
        # Возвращает np.ndarray [R, G, B] (0.0 - 1.0) или None
        color_np = obj.get_shading_for_face(poly, light_source, camera_pos)
        
        if color_np is not None:
            # Преобразуем цвет в формат Pygame (0-255)
            rgb = (
                min(255, int(color_np[0] * 255)),
                min(255, int(color_np[1] * 255)),
                min(255, int(color_np[2] * 255))
            )
            
            # Получаем 3D-центр полигона для Z-сортировки
            center_point = poly.get_center()
            center_3d_transformed = obj._transform_point(center_point)
            
            # Добавляем в список отрисовки: (Глубина Z, Полигон, Цвет)
            faces_to_draw.append({
                'z': center_3d_transformed[2],
                'polygon': poly,
                'color': rgb
            })
    
    # 2. Z-Сортировка: рисуем от дальних (больше Z) к ближним
    # Если в вашей системе координат Z растет от камеры, используйте reverse=False
    # Если Z растет вглубь сцены, используйте reverse=True
    faces_to_draw.sort(key=lambda k: k['z'], reverse=True)
    
    # 3. Отрисовка
    for item in faces_to_draw:
        points_2d = []
        
        # Получаем преобразованные вершины и проецируем их
        for v in item['polygon'].vertices:
            # Преобразование в мировые координаты
            v_3d_transformed = obj._transform_point(v) 
            # Проекция на 2D экран
            p_2d = project_vertex(v_3d_transformed, width, height)
            points_2d.append(p_2d)
            
        if len(points_2d) >= 3:
            pygame.draw.polygon(screen, item['color'], points_2d)
            # Опционально: контур
            # pygame.draw.polygon(screen, (50, 50, 50), points_2d, 1)