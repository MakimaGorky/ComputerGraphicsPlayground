
import pygame as pg


class Button:
    def __init__(self, rect, text, callback, font=None, color=(100,100,200), hover=(150,150,250)):
        self.rect = pg.Rect(rect)
        self.text = text
        self.callback = callback
        self.color = color
        self.hover = hover
        self.font = font or pg.font.SysFont(None, 28)
        self.is_hover = False

    def draw(self):
        pg.draw.rect(screen, self.hover if self.is_hover else self.color, self.rect, border_radius=8)
        text_surf = self.font.render(self.text, True, (255,255,255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def update(self, event):
        if event.type == pg.MOUSEMOTION:
            self.is_hover = self.rect.collidepoint(event.pos)
        elif event.type == pg.MOUSEBUTTONDOWN and self.is_hover:
            self.callback()