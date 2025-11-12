from primitives import *

def create_surface(func, x_range: Tuple[float, float], y_range: Tuple[float, float],
                   x_divisions: int, y_divisions: int) -> Object:
    """
    Создание поверхности по функции f(x, y) = z
    func: функция двух переменных
    x_range: (x0, x1)
    y_range: (y0, y1)
    x_divisions: количество разбиений по X
    y_divisions: количество разбиений по Y
    """
    x0, x1 = x_range
    y0, y1 = y_range

    x_step = (x1 - x0) / x_divisions
    y_step = (y1 - y0) / y_divisions

    # Создаем сетку точек
    points = []
    for i in range(y_divisions + 1):
        row = []
        y = y0 + i * y_step
        for j in range(x_divisions + 1):
            x = x0 + j * x_step
            try:
                z = func(x, y)
                row.append(Point(x, y, z))
            except:
                row.append(Point(x, y, 0))
        points.append(row)

    # Создаем грани
    obj = Object()
    for i in range(y_divisions):
        for j in range(x_divisions):
            # Четырехугольная грань
            p1 = points[i][j]
            p2 = points[i][j + 1]
            p3 = points[i + 1][j + 1]
            p4 = points[i + 1][j]

            obj.add_face(Polygon([p1, p2, p3, p4]))

    return obj