import numpy as np
import math
from primitives import *
import config
from typing import List, Tuple, Any, Optional
import os
from camera import *

# --- Вспомогательные функции ---

class LightSource:
    def __init__(self, position, color=(1.0, 1.0, 1.0)):
        self.position = np.array(position, dtype=float)
        self.color = np.array(color, dtype=float)

# Измените положение света, чтобы его было видно
single_light_source = LightSource((50, 50, -100), color=(1, 1, 1))

class LitObject(Object):
    def __init__(self, polygons: List[Polygon], color=(0.7, 0.7, 0.7), ambient_color=(0.1, 0.1, 0.1), color_specular=(1.0, 1.0, 1.0), shininess=100.0):
        super().__init__(polygons) 
        
        self.polygons = polygons
        
        # Параметры материала
        self.color_diffuse = np.array(color, dtype=float)
        self.color_specular = np.array(color_specular, dtype=float)
        self.color_ambient = np.array(ambient_color, dtype=float)
        self.shininess = shininess

        self.transform_matrix = np.identity(4)
        
        # Если нормалей нет вообще, считаем плоские
        self.calculate_normals()

    def _point_to_nparray(self, p: Point) -> np.ndarray:
        return np.array([p.x, p.y, p.z], dtype=float)
    
    def _nparray_to_point(self, n: np.ndarray) -> Point:
        return Point(n[0], n[1], n[2])

    def _transform_point(self, point: Point) -> np.ndarray:
        point_homogeneous = point.to_homogeneous()
        transformed_point = np.dot(self.transform_matrix, point_homogeneous)
        return transformed_point[:3] / transformed_point[3]

    def _transform_normal_vec(self, normal_vec: np.ndarray) -> np.ndarray:
        """Трансформирует вектор нормали (np.array)"""
        M_3x3 = self.transform_matrix[:3, :3]
        transformed_normal = np.dot(M_3x3, normal_vec)
        norm_magnitude = np.linalg.norm(transformed_normal)
        return transformed_normal / norm_magnitude if norm_magnitude != 0 else np.zeros(3)

    # --- Методы освещения ---

    def calculate_lambert_vertex(self, point_np, normal_np, light_source):
        """
        Расчет цвета вершины по модели Ламберта (только Diffuse)
        I = kd * Il * max(0, N.L)
        """
        L = light_source.position - point_np
        dist = np.linalg.norm(L)
        if dist != 0: L /= dist

        N_dot_L = np.dot(normal_np, L)
        diffuse = max(0.0, N_dot_L)

        # Ламберт обычно это Ambient + Diffuse
        color = self.color_ambient * light_source.color + \
                self.color_diffuse * light_source.color * diffuse

        return np.clip(color, 0.0, 1.0)

    def calculate_face_normal(self, poly: Polygon) -> np.ndarray:
        """
        Считает геометрическую нормаль (Flat), если нормалей вершин нет.
        """
        if len(poly.vertices) < 3:
            poly.normal = None
            return np.zeros(3)

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
        Если у полигона нет vertex_normals (из файла), считаем обычную нормаль грани.
        """
        for poly in self.polygons:
            # Если нет списка нормалей вершин, создаем геометрическую нормаль
            if not hasattr(poly, 'vertex_normals') or not poly.vertex_normals:
                self.calculate_face_normal(poly)
        
    def phong_shading(self, point: np.ndarray, normal: np.ndarray, light_source: LightSource, view_position: np.ndarray) -> np.ndarray:
        """
        Расчет цвета в конкретной точке
        """
        N = normal
        
        # Вектор к камере
        V = view_position - point
        dist_v = np.linalg.norm(V)
        if dist_v != 0: V = V / dist_v

        # Вектор к свету
        L = light_source.position - point
        dist_l = np.linalg.norm(L)
        if dist_l != 0: L = L / dist_l

        # 1. Ambient
        I_ambient = self.color_ambient * light_source.color

        # 2. Diffuse
        N_dot_L = np.dot(N, L)
        diffuse_intensity = max(0.0, N_dot_L)
        I_diffuse = self.color_diffuse * light_source.color * diffuse_intensity

        # 3. Specular
        if diffuse_intensity > 0:
            R = 2 * N_dot_L * N - L
            # R должен быть нормализован, хотя математически он сохраняет длину, 
            # из-за погрешностей float лучше нормализовать
            dist_r = np.linalg.norm(R)
            if dist_r != 0: R = R / dist_r
            
            R_dot_V = np.dot(R, V)
            specular_intensity = max(0.0, R_dot_V)**self.shininess
            I_specular = self.color_specular * light_source.color * specular_intensity
        else:
            I_specular = np.zeros(3)

        final_color = I_ambient + I_diffuse + I_specular
        return np.clip(final_color, 0.0, 1.0)
    
    
    def get_shading_for_face(self, poly: Polygon, light_source: LightSource, view_position: Tuple[float, float, float]) -> Optional[np.ndarray]:
        """
        Теперь поддерживает сглаживание!
        Если есть vertex_normals: считает свет в вершинах и усредняет ЦВЕТ.
        Если нет: считает свет в центре по нормали грани.
        """
        view_position_np = np.array(view_position, dtype=float)

        # ПРОВЕРКА: Есть ли у полигона нормали вершин (Smooth shading)
        if hasattr(poly, 'vertex_normals') and poly.vertex_normals and len(poly.vertex_normals) == len(poly.vertices):
            
            accumulated_color = np.zeros(3)
            
            # Проходим по каждой вершине треугольника
            for i in range(len(poly.vertices)):
                # 1. Координата вершины (World Space)
                vertex_pt = poly.vertices[i]
                vertex_pos = self._transform_point(vertex_pt)
                
                # 2. Нормаль вершины (World Space)
                # poly.vertex_normals хранит np.array, поэтому используем _transform_normal_vec
                raw_normal = poly.vertex_normals[i]
                vertex_normal = self._transform_normal_vec(raw_normal)
                
                # 3. Считаем цвет для этой вершины
                color_at_vertex = self.phong_shading(vertex_pos, vertex_normal, light_source, view_position_np)
                accumulated_color += color_at_vertex
            
            # Усредняем полученные цвета (Gouraud-style approximation for flat poly)
            final_color = accumulated_color / len(poly.vertices)
            return final_color

        else:
            # FALLBACK: Старый метод (Flat shading) по центру грани
            if poly.normal is None:
                return None
                
            center_point_primitives = poly.get_center()
            center_point_np = self._transform_point(center_point_primitives)
            
            # poly.normal это Point, используем старый метод _point_to_nparray внутри
            # Но для унификации лучше перевести в np.array и вызвать _transform_normal_vec
            normal_vec = self._point_to_nparray(poly.normal)
            face_normal_np = self._transform_normal_vec(normal_vec)

            return self.phong_shading(center_point_np, face_normal_np, light_source, view_position_np)

    # --- Метод загрузки OBJ ---
    
    @staticmethod
    def from_obj(filename, color=(0.7, 0.7, 0.7), position=(0,0,0), color_specular=(1.0, 1.0, 1.0), scale=1.0, shininess=100.0):
        vertices = []
        normals = [] 
        polygons = []

        try:
            scale_factor = config.OBJ_SCALE 
        except NameError:
            scale_factor = scale 

        try:
            with open(filename, 'r') as f:
                for line in f:
                    if line.startswith('v '):
                        parts = line.strip().split()
                        x, y, z = map(float, parts[1:4])
                        vertices.append(Point(
                            x * scale_factor + position[0], 
                            -y * scale_factor + position[1], 
                            z * scale_factor + position[2]
                        ))
                    
                    elif line.startswith('vn '):
                        parts = line.strip().split()
                        nx, ny, nz = map(float, parts[1:4])
                        n_vec = np.array([nx, ny, nz])
                        # Нормализуем при чтении
                        norm_len = np.linalg.norm(n_vec)
                        if norm_len != 0: n_vec /= norm_len
                        normals.append(n_vec)

                    elif line.startswith('f '):
                        parts = line.strip().split()[1:]
                        face_vertices = []
                        face_vertex_normals = [] # Храним нормали для КАЖДОЙ вершины грани

                        for part in parts:
                            vals = part.split('/')
                            # v index
                            v_idx = int(vals[0]) - 1
                            face_vertices.append(vertices[v_idx])
                            
                            # vn index
                            if len(vals) >= 3 and vals[2]:
                                vn_idx = int(vals[2]) - 1
                                face_vertex_normals.append(normals[vn_idx])

                        new_poly = Polygon(face_vertices)
                        
                        if len(face_vertex_normals) == len(face_vertices):
                            new_poly.vertex_normals = face_vertex_normals
                        else:
                            new_poly.vertex_normals = []

                        # Для совместимости с другой логикой (на всякий случай) оставим и old poly.normal
                        # как геометрическую нормаль, которую можно пересчитать позже
                        polygons.append(new_poly)

        except FileNotFoundError:
            print(f"Ошибка: Файл не найден по пути {filename}")
            return LitObject([]) 
        except Exception as e:
            print(f"Ошибка при чтении файла {filename}: {e}")
            return LitObject([])

        print(f"Модель {filename} успешно загружена. Полигонов: {len(polygons)}")
        return LitObject(polygons, color=color, color_specular=color_specular, shininess=shininess)

# --- Рендеринг ---

def project_vertex(v: np.ndarray, width: int, height: int) -> Tuple[int, int]:
    x, y, z = v
    fov = 600
    dist_z = -camera.z # Камера смотрит в -Z, поэтому инвертируем или сдвигаем мир
    
    # Простая защита от деления на ноль и точек за камерой
    if (dist_z - z) > 1:
        factor = fov / (dist_z - z)
    else:
        factor = 0.001 
    
    x_2d = x * factor + width / 2
    y_2d = -y * factor + height / 2 
    
    return int(x_2d), int(y_2d)


def render_lit_object(screen: pygame.Surface, obj: LitObject, light_source: LightSource, camera_pos: Tuple[float, float, float]):
    # Обновляем геометрические нормали для fallback режима (если вдруг vertex_normals нет)
    obj.calculate_normals() 
    
    width, height = screen.get_size()
    faces_to_draw = []
    
    for poly in obj.polygons:
        # Теперь метод get_shading_for_face сам решит:
        # использовать vertex_normals (сглаживание) или poly.normal (плоское)
        color_np = obj.get_shading_for_face(poly, light_source, camera_pos)
        
        if color_np is not None:
            rgb = (
                min(255, int(color_np[0] * 255)),
                min(255, int(color_np[1] * 255)),
                min(255, int(color_np[2] * 255))
            )
            
            center_point = poly.get_center()
            center_3d_transformed = obj._transform_point(center_point)
            
            faces_to_draw.append({
                'z': center_3d_transformed[2],
                'polygon': poly,
                'color': rgb
            })
    
    # Сортировка художника
    faces_to_draw.sort(key=lambda k: k['z'], reverse=True)
    
    for item in faces_to_draw:
        points_2d = []
        for v in item['polygon'].vertices:
            v_3d_transformed = obj._transform_point(v) 
            p_2d = project_vertex(v_3d_transformed, width, height)
            points_2d.append(p_2d)
            
        if len(points_2d) >= 3:
            pygame.draw.polygon(screen, item['color'], points_2d)