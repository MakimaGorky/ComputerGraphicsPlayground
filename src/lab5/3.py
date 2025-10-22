import pygame
import sys
from typing import List, Tuple, Optional

# Инициализация Pygame
pygame.init()

# Константы
WIDTH, HEIGHT = 1200, 800
BG_COLOR = (240, 240, 245)
POINT_COLOR = (50, 100, 255)
CONTROL_COLOR = (255, 100, 100)
LINE_COLOR = (200, 200, 200)
CURVE_COLOR = (50, 50, 50)
SELECTED_COLOR = (255, 200, 0)
TEXT_COLOR = (50, 50, 50)

POINT_RADIUS = 8
CONTROL_RADIUS = 6
CURVE_SEGMENTS = 50

class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.selected = False
    
    def pos(self) -> Tuple[float, float]:
        return (self.x, self.y)
    
    def distance_to(self, x: float, y: float) -> float:
        return ((self.x - x) ** 2 + (self.y - y) ** 2) ** 0.5

class BezierSegment:
    """Один сегмент кубической кривой Безье (4 точки)"""
    def __init__(self, p0: Point, p1: Point, p2: Point, p3: Point):
        self.p0 = p0  # Начальная опорная точка
        self.p1 = p1  # Первая контрольная точка
        self.p2 = p2  # Вторая контрольная точка
        self.p3 = p3  # Конечная опорная точка
    
    def get_point(self, t: float) -> Tuple[float, float]:
        """Вычислить точку на кривой для параметра t (0 <= t <= 1)"""
        t2 = t * t
        t3 = t2 * t
        mt = 1 - t
        mt2 = mt * mt
        mt3 = mt2 * mt
        
        x = mt3 * self.p0.x + 3 * mt2 * t * self.p1.x + 3 * mt * t2 * self.p2.x + t3 * self.p3.x
        y = mt3 * self.p0.y + 3 * mt2 * t * self.p1.y + 3 * mt * t2 * self.p2.y + t3 * self.p3.y
        
        return (x, y)
    
    def contains_point(self, point: Point) -> bool:
        """Проверить, содержит ли сегмент данную точку"""
        return point in [self.p0, self.p1, self.p2, self.p3]

class BezierSpline:
    def __init__(self):
        self.segments: List[BezierSegment] = []
        self.dragging_point: Optional[Point] = None
        self.last_anchor: Optional[Point] = None  # Последняя опорная точка
        
    def add_point(self, x: float, y: float):
        """Добавить новую опорную точку"""
        new_point = Point(x, y)
        
        if self.last_anchor is None:
            # Первая точка - просто сохраняем её
            self.last_anchor = new_point
        else:
            # Создаём новый сегмент от последней опорной точки
            dx = new_point.x - self.last_anchor.x
            dy = new_point.y - self.last_anchor.y
            
            # Создаём контрольные точки
            ctrl1 = Point(self.last_anchor.x + dx * 0.33, self.last_anchor.y + dy * 0.33)
            ctrl2 = Point(self.last_anchor.x + dx * 0.66, self.last_anchor.y + dy * 0.66)
            
            # Создаём новый сегмент
            segment = BezierSegment(self.last_anchor, ctrl1, ctrl2, new_point)
            self.segments.append(segment)
            
            # Обновляем последнюю опорную точку
            self.last_anchor = new_point
    
    def find_point_and_segment(self, x: float, y: float) -> Tuple[Optional[Point], Optional[BezierSegment]]:
        """Найти точку и сегмент, которому она принадлежит"""
        threshold = POINT_RADIUS + 5
        
        # Сначала проверяем последнюю опорную точку (если сегментов нет)
        if self.last_anchor and not self.segments:
            if self.last_anchor.distance_to(x, y) < threshold:
                return self.last_anchor, None
        
        # Проверяем все точки во всех сегментах
        for segment in self.segments:
            for point in [segment.p0, segment.p1, segment.p2, segment.p3]:
                if point.distance_to(x, y) < threshold:
                    return point, segment
        
        return None, None
    
    def remove_point(self, x: float, y: float) -> bool:
        """Удалить ближайшую точку"""
        point, segment = self.find_point_and_segment(x, y)
        
        if not point:
            return False
        
        # Если это одиночная опорная точка без сегментов
        if not segment and point == self.last_anchor:
            self.last_anchor = None
            return True
        
        if not segment:
            return False
        
        # Находим индекс сегмента
        seg_index = self.segments.index(segment)
        
        # Если это контрольная точка - удаляем только этот сегмент
        if point in [segment.p1, segment.p2]:
            self.segments.pop(seg_index)
            # Обновляем last_anchor
            if self.segments:
                self.last_anchor = self.segments[-1].p3
            else:
                self.last_anchor = segment.p0
            return True
        
        # Если это опорная точка - соединяем соседние сегменты
        # Удаляем исходящий сегмент и соединяем с предыдущим
        
        # Если это начальная точка самого первого сегмента
        if point == segment.p0 and seg_index == 0:
            # Просто удаляем этот сегмент
            self.segments.pop(seg_index)
            if self.segments:
                self.last_anchor = self.segments[-1].p3
            else:
                self.last_anchor = None
            return True
        
        # Если это конечная точка последнего сегмента
        if point == segment.p3 and seg_index == len(self.segments) - 1:
            # Удаляем этот сегмент
            self.segments.pop(seg_index)
            if self.segments:
                self.last_anchor = self.segments[-1].p3
            else:
                self.last_anchor = segment.p0
            return True
        
        # Если это промежуточная опорная точка
        # Находим все сегменты, которые используют эту точку
        segments_with_point = []
        for i, seg in enumerate(self.segments):
            if seg.p0 == point or seg.p3 == point:
                segments_with_point.append((i, seg))
        
        if len(segments_with_point) == 2:
            # Точка соединяет два сегмента
            idx1, seg1 = segments_with_point[0]
            idx2, seg2 = segments_with_point[1]
            
            # Создаём новый сегмент, соединяющий начало первого и конец второго
            if seg1.p3 == point and seg2.p0 == point:
                # seg1 -> point -> seg2
                # Создаём новый сегмент от seg1.p0 до seg2.p3
                dx = seg2.p3.x - seg1.p0.x
                dy = seg2.p3.y - seg1.p0.y
                new_ctrl1 = Point(seg1.p0.x + dx * 0.33, seg1.p0.y + dy * 0.33)
                new_ctrl2 = Point(seg1.p0.x + dx * 0.66, seg1.p0.y + dy * 0.66)
                new_segment = BezierSegment(seg1.p0, new_ctrl1, new_ctrl2, seg2.p3)
                
                # Удаляем оба старых сегмента (удаляем с конца, чтобы не сбить индексы)
                if idx1 > idx2:
                    self.segments.pop(idx1)
                    self.segments.pop(idx2)
                    self.segments.insert(idx2, new_segment)
                else:
                    self.segments.pop(idx2)
                    self.segments.pop(idx1)
                    self.segments.insert(idx1, new_segment)
                
                # Обновляем last_anchor
                if self.segments:
                    self.last_anchor = self.segments[-1].p3
                else:
                    self.last_anchor = None
                
                return True
        elif len(segments_with_point) == 1:
            # Точка используется только в одном сегменте - просто удаляем его
            idx, seg = segments_with_point[0]
            self.segments.pop(idx)
            if self.segments:
                self.last_anchor = self.segments[-1].p3
            else:
                if seg.p0 == point:
                    self.last_anchor = seg.p3
                else:
                    self.last_anchor = seg.p0
            return True
        
        return False
    
    def start_drag(self, x: float, y: float):
        """Начать перетаскивание точки"""
        point, _ = self.find_point_and_segment(x, y)
        if point:
            self.dragging_point = point
            point.selected = True
    
    def drag(self, x: float, y: float):
        """Перетащить точку"""
        if self.dragging_point:
            self.dragging_point.x = x
            self.dragging_point.y = y
    
    def stop_drag(self):
        """Остановить перетаскивание"""
        if self.dragging_point:
            self.dragging_point.selected = False
            self.dragging_point = None
    
    def draw(self, surface: pygame.Surface):
        """Отрисовать сплайн"""
        # Рисуем все сегменты
        for segment in self.segments:
            # Рисуем контрольные линии
            pygame.draw.line(surface, LINE_COLOR, segment.p0.pos(), segment.p1.pos(), 1)
            pygame.draw.line(surface, LINE_COLOR, segment.p2.pos(), segment.p3.pos(), 1)
            
            # Рисуем кривую
            curve_points = []
            for i in range(CURVE_SEGMENTS + 1):
                t = i / CURVE_SEGMENTS
                point = segment.get_point(t)
                curve_points.append(point)
            
            if len(curve_points) > 1:
                pygame.draw.lines(surface, CURVE_COLOR, False, curve_points, 3)
            
            # Рисуем контрольные точки
            for ctrl_point in [segment.p1, segment.p2]:
                color = SELECTED_COLOR if ctrl_point.selected else CONTROL_COLOR
                pygame.draw.circle(surface, color, (int(ctrl_point.x), int(ctrl_point.y)), CONTROL_RADIUS)
                pygame.draw.circle(surface, (255, 255, 255), (int(ctrl_point.x), int(ctrl_point.y)), CONTROL_RADIUS - 2)
            
            # Рисуем опорные точки
            for anchor_point in [segment.p0, segment.p3]:
                color = SELECTED_COLOR if anchor_point.selected else POINT_COLOR
                pygame.draw.circle(surface, color, (int(anchor_point.x), int(anchor_point.y)), POINT_RADIUS)
                pygame.draw.circle(surface, (255, 255, 255), (int(anchor_point.x), int(anchor_point.y)), POINT_RADIUS - 2)
        
        # Рисуем одиночную опорную точку, если есть
        if self.last_anchor and not self.segments:
            color = SELECTED_COLOR if self.last_anchor.selected else POINT_COLOR
            pygame.draw.circle(surface, color, (int(self.last_anchor.x), int(self.last_anchor.y)), POINT_RADIUS)
            pygame.draw.circle(surface, (255, 255, 255), (int(self.last_anchor.x), int(self.last_anchor.y)), POINT_RADIUS - 2)

def draw_instructions(surface: pygame.Surface, font: pygame.font.Font):
    """Отрисовать инструкции"""
    instructions = [
        "ЛКМ - добавить опорную точку",
        "ПКМ - удалить точку",
        "Перетаскивание - переместить точку",
        "ESC - очистить всё",
        "Q - выход"
    ]
    
    y_offset = 10
    for text in instructions:
        rendered = font.render(text, True, TEXT_COLOR)
        surface.blit(rendered, (10, y_offset))
        y_offset += 30

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Кубические сплайны Безье")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    
    spline = BezierSpline()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    spline.segments.clear()
                    spline.last_anchor = None
                elif event.key == pygame.K_q:
                    running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                
                if event.button == 1:  # ЛКМ
                    # Проверяем, не начинаем ли мы перетаскивание
                    point, _ = spline.find_point_and_segment(x, y)
                    if point:
                        spline.start_drag(x, y)
                    else:
                        spline.add_point(x, y)
                
                elif event.button == 3:  # ПКМ
                    spline.remove_point(x, y)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    spline.stop_drag()
            
            elif event.type == pygame.MOUSEMOTION:
                if spline.dragging_point:
                    x, y = event.pos
                    spline.drag(x, y)
        
        # Отрисовка
        screen.fill(BG_COLOR)
        spline.draw(screen)
        draw_instructions(screen, font)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
