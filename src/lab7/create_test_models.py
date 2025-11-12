"""
Скрипт для создания тестовых OBJ файлов
Запустите этот скрипт, чтобы создать примеры моделей для тестирования
"""

from D3Renderer import *
from primitives import *
from transformations import *
from object_IO import *
from rotation_figure import *
from surface_2d import *


def create_test_models():
    """Создает различные тестовые модели и сохраняет их в OBJ формате"""

    print("=== СОЗДАНИЕ ТЕСТОВЫХ МОДЕЛЕЙ ===\n")

    # 1. Многогранники из Лаб. 6
    print("1. Создание многогранников...")

    cube = create_cube()
    save_obj(cube, "cube.obj")

    tetra = create_tetrahedron()
    save_obj(tetra, "tetrahedron.obj")

    octa = create_octahedron()
    save_obj(octa, "octahedron.obj")

    ico = create_icosahedron()
    save_obj(ico, "icosahedron.obj")

    dodeca = create_dodecahedron()
    save_obj(dodeca, "dodecahedron.obj")

    print("✓ Многогранники сохранены\n")

    # 2. Фигуры вращения
    print("2. Создание фигур вращения...")

    # Ваза
    vase_profile = create_vase_profile()
    vase = create_rotation_figure(vase_profile, 'Y', 16)
    save_obj(vase, "vase.obj")

    # Цилиндр
    cylinder_profile = [Point(50, i * 20 - 100, 0) for i in range(11)]
    cylinder = create_rotation_figure(cylinder_profile, 'Y', 12)
    save_obj(cylinder, "cylinder.obj")

    # Конус
    cone_profile = [Point(100 - i * 10, i * 20 - 100, 0) for i in range(11)]
    cone = create_rotation_figure(cone_profile, 'Y', 16)
    save_obj(cone, "cone.obj")

    # Сфера (вращение полукруга)
    sphere_profile = []
    for i in range(21):
        angle = np.pi * i / 20
        x = 80 * np.sin(angle)
        y = 80 * np.cos(angle)
        sphere_profile.append(Point(x, y, 0))
    sphere = create_rotation_figure(sphere_profile, 'Y', 20)
    save_obj(sphere, "sphere.obj")

    # Тор (вращение окружности вокруг оси Y)
    torus_profile = []
    R = 80  # Большой радиус
    r = 30  # Малый радиус
    for i in range(20):
        angle = 2 * np.pi * i / 20
        x = R + r * np.cos(angle)
        y = r * np.sin(angle)
        torus_profile.append(Point(x, y, 0))
    torus = create_rotation_figure(torus_profile, 'Y', 24)
    save_obj(torus, "torus.obj")

    print("✓ Фигуры вращения сохранены\n")

    # 3. Графики функций
    print("3. Создание графиков функций...")

    # sin(x) * cos(y)
    surface1 = create_surface(func_sin_cos, (-5, 5), (-5, 5), 25, 25)
    save_obj(surface1, "surface_sin_cos.obj")

    # Параболоид
    surface2 = create_surface(func_paraboloid, (-5, 5), (-5, 5), 20, 20)
    save_obj(surface2, "surface_paraboloid.obj")

    # Седло
    surface3 = create_surface(func_saddle, (-5, 5), (-5, 5), 20, 20)
    save_obj(surface3, "surface_saddle.obj")

    # Волна
    surface4 = create_surface(func_wave, (-10, 10), (-10, 10), 30, 30)
    save_obj(surface4, "surface_wave.obj")

    # Дополнительные функции

    # Гауссова колокообразная функция
    def func_gaussian(x, y):
        return 100 * np.exp(-(x ** 2 + y ** 2) / 10)

    surface5 = create_surface(func_gaussian, (-5, 5), (-5, 5), 25, 25)
    save_obj(surface5, "surface_gaussian.obj")

    # Сложная волна
    def func_complex_wave(x, y):
        return 30 * (np.sin(x) + np.cos(y))

    surface6 = create_surface(func_complex_wave, (-5, 5), (-5, 5), 25, 25)
    save_obj(surface6, "surface_complex_wave.obj")

    print("✓ Графики функций сохранены\n")

    # 4. Пользовательские фигуры вращения
    print("4. Создание пользовательских фигур...")

    # Бокал
    glass_profile = []
    for i in range(15):
        t = i / 14.0
        y = t * 150 - 75

        if t < 0.2:
            x = 10 + t * 50
        elif t < 0.3:
            x = 20
        elif t < 0.8:
            x = 20 + (t - 0.3) * 60
        else:
            x = 50 + (t - 0.8) * 50

        glass_profile.append(Point(x, y, 0))

    glass = create_rotation_figure(glass_profile, 'Y', 20)
    save_obj(glass, "glass.obj")

    # Колокол
    bell_profile = []
    for i in range(20):
        t = i / 19.0
        y = t * 120 - 60

        if t < 0.1:
            x = 5
        else:
            angle = (t - 0.1) * np.pi / 2
            x = 5 + 60 * np.sin(angle)

        bell_profile.append(Point(x, y, 0))

    bell = create_rotation_figure(bell_profile, 'Y', 24)
    save_obj(bell, "bell.obj")

    print("✓ Пользовательские фигуры сохранены\n")

    print("=== ВСЕ МОДЕЛИ СОЗДАНЫ ===")
    print("\nСозданные файлы:")
    print("Многогранники: cube.obj, tetrahedron.obj, octahedron.obj, icosahedron.obj, dodecahedron.obj")
    print("Фигуры вращения: vase.obj, cylinder.obj, cone.obj, sphere.obj, torus.obj, glass.obj, bell.obj")
    print("Графики: surface_sin_cos.obj, surface_paraboloid.obj, surface_saddle.obj, surface_wave.obj,")
    print("         surface_gaussian.obj, surface_complex_wave.obj")
    print("\nИспользуйте эти файлы для тестирования загрузки в основной программе!")


def demonstrate_rotation_figure():
    """Демонстрация создания фигуры вращения с пользовательскими параметрами"""

    print("\n=== ДЕМОНСТРАЦИЯ ФИГУРЫ ВРАЩЕНИЯ ===\n")

    # Пример 1: Образующая - прямая линия (цилиндр)
    print("Пример 1: Цилиндр (прямая линия)")
    profile1 = [Point(50, i * 10, 0) for i in range(11)]

    print("Вращение вокруг оси Y с 8 разбиениями:")
    fig1 = create_rotation_figure(profile1, 'Y', 8)
    save_obj(fig1, "demo_cylinder_8.obj")

    print("Вращение вокруг оси Y с 16 разбиениями:")
    fig2 = create_rotation_figure(profile1, 'Y', 16)
    save_obj(fig2, "demo_cylinder_16.obj")

    # Пример 2: Образующая - синусоида
    print("\nПример 2: Волнистая поверхность")
    profile2 = []
    for i in range(21):
        y = i * 10
        x = 50 + 20 * np.sin(i * 0.5)
        profile2.append(Point(x, y, 0))

    fig3 = create_rotation_figure(profile2, 'Y', 20)
    save_obj(fig3, "demo_wavy.obj")

    # Пример 3: Разные оси вращения
    print("\nПример 3: Вращение вокруг разных осей")
    profile3 = [Point(30 + i * 5, 50, i * 10) for i in range(11)]

    fig4 = create_rotation_figure(profile3, 'X', 12)
    save_obj(fig4, "demo_rotate_x.obj")

    fig5 = create_rotation_figure(profile3, 'Y', 12)
    save_obj(fig5, "demo_rotate_y.obj")

    fig6 = create_rotation_figure(profile3, 'Z', 12)
    save_obj(fig6, "demo_rotate_z.obj")

    print("\n✓ Демонстрационные фигуры созданы")


def demonstrate_surface():
    """Демонстрация создания графиков функций"""

    print("\n=== ДЕМОНСТРАЦИЯ ГРАФИКОВ ФУНКЦИЙ ===\n")

    # Пример с разными разбиениями
    print("Параболоид с разным количеством разбиений:")

    surf1 = create_surface(func_paraboloid, (-5, 5), (-5, 5), 10, 10)
    save_obj(surf1, "demo_paraboloid_10.obj")
    print("- 10x10 разбиений")

    surf2 = create_surface(func_paraboloid, (-5, 5), (-5, 5), 20, 20)
    save_obj(surf2, "demo_paraboloid_20.obj")
    print("- 20x20 разбиений")

    surf3 = create_surface(func_paraboloid, (-5, 5), (-5, 5), 40, 40)
    save_obj(surf3, "demo_paraboloid_40.obj")
    print("- 40x40 разбиений")

    # Пример с разными диапазонами
    print("\nВолна с разными диапазонами:")

    surf4 = create_surface(func_wave, (-5, 5), (-5, 5), 20, 20)
    save_obj(surf4, "demo_wave_small.obj")
    print("- Диапазон [-5, 5]")

    surf5 = create_surface(func_wave, (-15, 15), (-15, 15), 40, 40)
    save_obj(surf5, "demo_wave_large.obj")
    print("- Диапазон [-15, 15]")

    print("\n✓ Демонстрационные графики созданы")


def test_load_save():
    """Тестирование загрузки и сохранения"""

    print("\n=== ТЕСТ ЗАГРУЗКИ И СОХРАНЕНИЯ ===\n")

    # Создаем оригинальную модель
    print("1. Создание оригинальной модели (икосаэдр)...")
    original = create_icosahedron()
    save_obj(original, "test_original.obj")
    print(f"   Граней в оригинале: {len(original.polygons)}")

    # Загружаем её обратно
    print("\n2. Загрузка модели из файла...")
    loaded = load_obj("test_original.obj")
    print(f"   Граней после загрузки: {len(loaded.polygons)}")

    # Применяем преобразование
    print("\n3. Применение преобразований...")
    rotate_around_center(loaded, 'Y', np.radians(45))
    scale_relative_to_center(loaded, 1.5, 1.5, 1.5)

    # Сохраняем трансформированную модель
    print("\n4. Сохранение трансформированной модели...")
    save_obj(loaded, "test_transformed.obj")

    print("\n✓ Тест завершен успешно!")
    print("Файлы: test_original.obj, test_transformed.obj")


if __name__ == "__main__":
    print("=" * 60)
    print("ГЕНЕРАТОР ТЕСТОВЫХ 3D МОДЕЛЕЙ")
    print("=" * 60)

    create_test_models()
    demonstrate_rotation_figure()
    demonstrate_surface()
    test_load_save()

    print("\n" + "=" * 60)
    print("ГОТОВО! Все тестовые модели созданы.")
    print("Теперь вы можете:")
    print("1. Запустить D3Renderer.py")
    print("2. Использовать кнопку 'Загрузить OBJ' для загрузки моделей")
    print("3. Применять аффинные преобразования")
    print("4. Сохранять результаты с помощью 'Сохранить OBJ'")
    print("=" * 60)