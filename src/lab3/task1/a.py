"""
1а) Рекурсивный алгоритм заливки на основе серий пикселов (линий)
    заданным цветом.
"""
import numpy as np
import pygame as pg
import os  # просто будь собой бро
import sys  # просто будь собой бро
sys.path.append("libs")
from ImagesLoader import *


sys.setrecursionlimit(10000)


class Filler:
    """
    Просматривает линии и возвращает их
    """
    def __init__(self, screen, assets_path='coloring_pages'):
        self.images_loader = ImagesLoader(screen, assets_path)
        self.image = self.images_loader.get_image()
        self.width, self.height = self.image.get_size()
        self.screen = screen
        self.image_offset = (100, 100)
        self.have_clicked = False

    def get_line(self, x, y):
        left = x
        while left >= 0 and self.image.get_at((left, y)) == self.original_color:
            left -= 1
        right = x
        while right < self.width and self.image.get_at((right, y)) == self.original_color:
            right += 1
        return left+1, right-1

    def repaint_line(self, left, right, y):
        for x in range(left, right + 1):
            self.used[x][y] = True
            self.image.set_at((x, y), self.repaint_function(x, y))

    def run(self, repaint_function):
        x0, y0 = self.have_clicked_at
        self.used = [[False] * self.height for _ in range(self.width)]
        self.repaint_function = repaint_function
        self.original_color = self.image.get_at((x0, y0))
        self._run(x0, y0)

    def _run(self, x, y):
        if self.used[x][y] or self.image.get_at((x, y)) != self.original_color:
            return
        left, right = self.get_line(x, y)
        self.repaint_line(left, right, y)
        for x in range(left, right + 1):
            if 0 <= y-1 < self.height and not self.used[x][y-1]:
                self._run(x, y-1)
            if 0 <= y+1 < self.height and not self.used[x][y+1]:
                self._run(x, y+1)

    def update(self, event):
        self.images_loader.update(event)
        if self.images_loader.have_changed:
            self.image = self.images_loader.get_image()
            self.width, self.height = self.image.get_size()

        self.have_clicked = False
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:  # левая кнопка
            mx, my = event.pos
            img_x = mx - self.image_offset[0]
            img_y = my - self.image_offset[1]
            if 0 <= img_x < self.width and 0 <= img_y < self.height:
                self.have_clicked = True
                self.have_clicked_at = (img_x, img_y)

    def draw(self):
        self.images_loader.draw()
        screen.blit(self.image, self.image_offset)


def to_cyan(x, y):
    return (0, 255, 255)


if __name__ == '__main__':
    pg.init()
    screen_size = (240*5, 136*5)
    screen = pg.display.set_mode(screen_size, pg.RESIZABLE)
    clock = pg.time.Clock()

    filler = Filler(screen)

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                # print(*fd.debug)
                pg.quit()
                sys.exit()
            if event.type == pg.VIDEORESIZE:
                screen_size = (event.w, event.h)
            filler.update(event)
            # if images_loader.have_changed:
            #     image = images_loader.get_image()
                # surf = pg.surfarray.make_surface(np.transpose(image, (1,0,2)).swapaxes(0,1))

        if filler.have_clicked:
            filler.run(to_cyan)

        screen.fill((30, 30, 30))
        filler.draw()
        # images_loader.draw()
        # screen.blit(image, (100, 100))
        pg.display.flip()
        clock.tick(20)

