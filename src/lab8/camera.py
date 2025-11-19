import pygame

class Camera:
    def __init__(self, x, y, z, dx=5, dy=5, dz=5):
        self.x = x
        self.y = y
        self.z = z
        self.dx = dx
        self.dy = dy
        self.dz = dz

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LSHIFT]:
            # Движение по X и Z (вглубь/из глубины)
            if keys[pygame.K_RIGHT]:
                self.x += self.dx
            if keys[pygame.K_LEFT]:
                self.x -= self.dx
            if keys[pygame.K_UP]:
                self.z += self.dz
            if keys[pygame.K_DOWN]:
                self.z -= self.dz
        else:
            # Движение по X и Y (плоское смещение камеры)
            if keys[pygame.K_RIGHT]:
                self.x += self.dx
            if keys[pygame.K_LEFT]:
                self.x -= self.dx
            if keys[pygame.K_UP]:
                self.y -= self.dy # Инвертируем Y для привычного управления (вверх -> камера вверх)
            if keys[pygame.K_DOWN]:
                self.y += self.dy


# Начальные координаты камеры
camera = Camera(1000, 650, -1500)