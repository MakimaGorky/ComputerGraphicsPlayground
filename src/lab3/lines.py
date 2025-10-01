import random
import pygame as pg
import os
import numpy as np
import matplotlib.pyplot as plt
from pygame.locals import *

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
Image_list = [
    os.path.join(base_dir, "assets", "house1.jpg"),
    os.path.join(base_dir, "assets", "house2.jpg"),
    os.path.join(base_dir, "assets", "house3.jpg"),
    os.path.join(base_dir, "assets", "house4.jpg"),
    # os.path.join(base_dir, "assets", "win1984.png"),
    # os.path.join(base_dir, "assets", "win2077.jpg"),
]

def nothing():
    return
def scale(point, rect):
    new_point = ((point[0]-rect.x) // 5, (point[1]-rect.y) // 5)
    return new_point

class Button:
    def __init__(self, rect, text, callback, screen, font=None, color=(100,100,200), hover=(150,150,250)):
        self.rect = pg.Rect(rect)
        self.text = text
        self.callback = callback
        self.screen = screen
        self.color = color
        self.hover = hover
        self.font = font or pg.font.SysFont(None, 28)
        self.is_hover = False
        self.is_always_hover = False

    def draw(self):
        pg.draw.rect(self.screen, self.hover if (self.is_hover or self.is_always_hover) else self.color, self.rect, border_radius=8)
        text_surf = self.font.render(self.text, True, (255,255,255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        self.screen.blit(text_surf, text_rect)

    def update(self, event):
        if event.type == pg.MOUSEMOTION:
            self.is_hover = self.rect.collidepoint(event.pos)
        elif event.type == pg.MOUSEBUTTONDOWN and self.is_hover:
            self.callback()

class Canvas:
    def __init__(self, rect, screen, color=(255,255,255)):
        self.color = color
        self.line_color = (0,0,0)
        self.rect = pg.Rect(rect)
        self.img = pg.Surface((100,100))
        self.img.fill(color)
        self.screen = screen
        self.is_first_point = True

    def draw(self):
        scaled_img_surf = pg.transform.scale(
                    self.img,
                    (self.rect.width, self.rect.height)
                )
        self.screen.blit(scaled_img_surf, (self.rect.x, self.rect.y))

    def clear(self):
        self.img.fill(self.color)

    def draw_pixel_alpha(self, point, color, alpha):
        old_color = self.img.get_at(point)
        new_color = (
                    int(old_color[0] * (1 - alpha) + color[0] * alpha),
                    int(old_color[1] * (1 - alpha) + color[1] * alpha),
                    int(old_color[2] * (1 - alpha) + color[2] * alpha)
                    )
        self.img.set_at(point, new_color)


    def change_method_bresenham(self):
        self.draw_line = self.draw_line_bresenham
        self.bresenham_button.is_always_hover = True
        self.wu_button.is_always_hover = False
        self.is_first_point = True

    def change_method_wu(self):
        self.draw_line = self.draw_line_wu
        self.bresenham_button.is_always_hover = False
        self.wu_button.is_always_hover = True
        self.is_first_point = True

    def draw_line_bresenham(self, point1, point2):
        deltax = np.abs(point2[0]-point1[0])
        deltay = np.abs(point2[1]-point1[1])
        error = 0
        if deltax > deltay: #Если линию клонит к OX, проходимся циклом по x, если к OY - по y
            if point1[0]>point2[0]: #проверяем чтобы point1 был левее point2
                point1, point2 = point2, point1
            deltaerr = deltay + 1
            y = point1[1]

            diry = point1[1]-point2[1] #Определяем направление движения по y
            if diry < 0:
                diry = 1
            elif diry > 0:
                diry = -1
            
            for x in range(point1[0], point2[0]+1): #Проходимся по x
                self.img.set_at((x,y), self.line_color)
                error = error + deltaerr
                if error >= deltax+1:
                    y = y+diry
                    error = error - (deltax+1)
        else:
            if point1[1]>point2[1]: #проверяем чтобы point1 был ниже point2
                point1, point2 = point2, point1
            deltaerr = deltax + 1
            x = point1[0]

            dirx = point1[0]-point2[0] #Определяем направление движения по x
            if dirx < 0:
                dirx = 1
            elif dirx > 0:
                dirx = -1
            
            for y in range(point1[1], point2[1]+1):#Проходимся по y
                self.img.set_at((x,y), self.line_color)
                error = error + deltaerr
                if error >= deltay+1:
                    x = x+dirx
                    error = error - (deltay+1)

    def draw_line_wu(self, point1, point2):
        deltax = np.abs(point2[0]-point1[0])
        deltay = np.abs(point2[1]-point1[1])
        if deltax > deltay: #Если линию клонит к OX, проходимся циклом по x, если к OY - по y
            if point1[0]>point2[0]: #проверяем чтобы point1 был левее point2
                point1, point2 = point2, point1

            y = point1[1]

            diry = point1[1]-point2[1] #Определяем направление движения по y
            if diry < 0:
                diry = deltay/deltax
            elif diry > 0:
                diry = -deltay/deltax
            
            for x in range(point1[0], point2[0]+1): #Проходимся по x
                self.draw_pixel_alpha((x,int(y)+1), self.line_color, (y - int(y)))
                self.draw_pixel_alpha((x,int(y)), self.line_color, 1-(y - int(y)))
                y = y+diry 
        else:
            if point1[1]>point2[1]: #проверяем чтобы point1 был ниже point2
                point1, point2 = point2, point1
            
            x = point1[0]

            dirx = point1[0]-point2[0] #Определяем направление движения по x
            if dirx < 0:
                dirx = deltax/deltay
            elif dirx > 0:
                dirx = -deltax/deltay
            
            for y in range(point1[1], point2[1]+1):#Проходимся по y
                self.draw_pixel_alpha((int(x)+1, y), self.line_color, (x - int(x)))
                self.draw_pixel_alpha((int(x), y), self.line_color, 1-(x - int(x)))
                x = x+dirx 

    def add_point(self, point):
        if self.is_first_point:
            self.first_point = point
        else:
            point1 = scale(self.first_point, self.rect)
            point2 = scale(point, self.rect)
            self.draw_line(point2, point1)

        self.is_first_point = not self.is_first_point

    def update(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.add_point(event.pos)
        return



class App:
    def __init__(self, width=540, height=590, caption="Liner"):
        """
        Sample App
        Args:
            width: очевидно
            height: нетрудно догадаться
            caption: оставим читателю, как упражнение

        :return: 😂😂😂
        """
        pg.init()
        self.width, self.height = width, height
        self.screen = pg.display.set_mode((self.width, self.height))
        pg.display.set_caption(caption)

        # Цвета
        self.colors = {
            'background': (40, 44, 52),
            'panel': (30, 34, 42),
            'text': (220, 220, 220),
            'border': (80, 85, 95),
            'highlight': (97, 175, 239),
            'button': (150,150,250)
        }

        # Шрифты
        self.font_large = pg.font.Font(None, 32)
        self.font_medium = pg.font.Font(None, 24)
        self.font_small = pg.font.Font(None, 18)

        # Всё что надо отрисовывать и отслеживать события
        self.drawables = []
        self.updateables = []

        # Позиции и размеры
        self.margin = 20

        # Кнопки и канвасы
        canvas = Canvas((20, 70, 500, 500), self.screen)
        self.drawables.append(canvas)
        self.updateables.append(canvas)
        button1 = Button((20, 20, 120, 30), "Bresenham", canvas.change_method_bresenham, self.screen)
        self.drawables.append(button1)
        self.updateables.append(button1)
        button2 = Button((160, 20, 120, 30), "Wu", canvas.change_method_wu, self.screen)
        self.drawables.append(button2)
        self.updateables.append(button2)
        button3 = Button((460, 20, 60, 30), "Clear", canvas.clear, self.screen)
        self.drawables.append(button3)
        self.updateables.append(button3)

        canvas.bresenham_button = button1
        canvas.wu_button = button2
        canvas.change_method_bresenham()

        # Флаги состояния
        self.running = False

    def draw(self):
        """
        Отрисовка интерфейса
        """
        # Очищаем экран
        self.screen.fill(self.colors['background'])

        # Рисуем всё что рисуется:
        for drawable in self.drawables:
            drawable.draw()

    def handle_events(self):
        """
        Обработка событий
        """
        for event in pg.event.get():
            for updateable in self.updateables:
                updateable.update(event)

            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                self.running = False

    def main_loop(self):
        self.running = True
        clock = pg.time.Clock()

        while self.running:
            self.handle_events()
            self.draw() 
            pg.display.flip()
            clock.tick(60)

        pg.quit()


if __name__ == '__main__':
    app = App()
    app.main_loop()