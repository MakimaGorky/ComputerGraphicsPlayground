import pygame
import sys
from typing import List, Tuple

# Инициализация pygame
pygame.init()

# Константы
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 100, 255)
GREEN = (0, 200, 0)
GRAY = (200, 200, 200)
POINT_RADIUS = 5
LINE_WIDTH = 2

# Создание окна
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("QuickHull Algorithm Playground")
clock = pygame.time.Clock()

# Шрифт для текста
font = pygame.font.Font(None, 24)

# Глобальные переменные
points = []
hull = []


def cross_product(o: Tuple[int, int], a: Tuple[int, int], b: Tuple[int, int]) -> float:
    """Вычисляет векторное произведение векторов OA и OB"""
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def distance_to_line(point: Tuple[int, int], line_start: Tuple[int, int],
                     line_end: Tuple[int, int]) -> float:
    """Вычисляет расстояние от точки до линии"""
    return abs(cross_product(line_start, line_end, point))


def find_hull(points_set: List[Tuple[int, int]], p1: Tuple[int, int],
              p2: Tuple[int, int]) -> List[Tuple[int, int]]:
    """
    Рекурсивная функция QuickHull
    Находит точки выпуклой оболочки с одной стороны от линии p1-p2
    """
    if not points_set:
        return []

    # Находим самую дальнюю точку от линии p1-p2
    max_dist = 0
    farthest_point = None

    for point in points_set:
        dist = distance_to_line(point, p1, p2)
        if dist > max_dist:
            max_dist = dist
            farthest_point = point

    if farthest_point is None:
        return []

    # Разделяем оставшиеся точки на две группы
    left_set = []
    right_set = []

    for point in points_set:
        if point == farthest_point:
            continue

        # Проверяем, с какой стороны от новых линий находится точка
        if cross_product(p1, farthest_point, point) > 0:
            left_set.append(point)
        elif cross_product(farthest_point, p2, point) > 0:
            right_set.append(point)

    # Рекурсивно обрабатываем обе части
    left_hull = find_hull(left_set, p1, farthest_point)
    right_hull = find_hull(right_set, farthest_point, p2)

    # Объединяем результаты
    return left_hull + [farthest_point] + right_hull


def quickhull(points: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Основная функция алгоритма QuickHull
    Возвращает список точек выпуклой оболочки в порядке обхода
    """
    if len(points) < 3:
        return points

    # Находим крайние точки (самая левая и самая правая)
    min_point = min(points, key=lambda p: (p[0], p[1]))
    max_point = max(points, key=lambda p: (p[0], -p[1]))

    if min_point == max_point:
        return [min_point]

    # Разделяем точки на две группы: выше и ниже линии min-max
    upper_set = []
    lower_set = []

    for point in points:
        if point == min_point or point == max_point:
            continue

        cp = cross_product(min_point, max_point, point)
        if cp > 0:
            upper_set.append(point)
        elif cp < 0:
            lower_set.append(point)

    # Находим выпуклую оболочку для верхней и нижней частей
    upper_hull = find_hull(upper_set, min_point, max_point)
    lower_hull = find_hull(lower_set, max_point, min_point)

    # Объединяем результаты
    return [min_point] + upper_hull + [max_point] + lower_hull


def draw_instructions():
    """Отрисовка инструкций"""
    instructions = [
        "ЛКМ - добавить точку",
        "C - очистить все",
        "ESC - выход"
    ]

    y_offset = 10
    for instruction in instructions:
        text = font.render(instruction, True, BLACK)
        screen.blit(text, (10, y_offset))
        y_offset += 25


def draw_hull(hull_points: List[Tuple[int, int]]):
    """Отрисовка выпуклой оболочки"""
    if len(hull_points) < 2:
        return

    # Рисуем полигон
    if len(hull_points) >= 3:
        pygame.draw.polygon(screen, GREEN, hull_points, LINE_WIDTH)

    # Рисуем линии
    for i in range(len(hull_points)):
        start = hull_points[i]
        end = hull_points[(i + 1) % len(hull_points)]
        pygame.draw.line(screen, BLUE, start, end, LINE_WIDTH)


def draw_points(points_list: List[Tuple[int, int]]):
    """Отрисовка точек"""
    for point in points_list:
        pygame.draw.circle(screen, RED, point, POINT_RADIUS)


def main():
    global points, hull

    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Левая кнопка мыши
                    # Добавляем точку
                    points.append(event.pos)
                    # Пересчитываем оболочку
                    hull = quickhull(points)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    # Очистка всех точек
                    points = []
                    hull = []
                elif event.key == pygame.K_ESCAPE:
                    running = False

        # Отрисовка
        screen.fill(WHITE)

        # Рисуем выпуклую оболочку
        if hull:
            draw_hull(hull)

        # Рисуем точки
        draw_points(points)

        # Рисуем инструкции
        draw_instructions()

        # Показываем количество точек
        count_text = font.render(f"Точек: {len(points)}", True, BLACK)
        screen.blit(count_text, (WIDTH - 120, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()