
import pygame
import math

class Camera:
    def __init__(self, x, y, z, dx=5, dy=5, dz=5):
        self.x = x
        self.y = y
        self.z = z
        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.angle_x = 0.0
        self.angle_y = 0.0
        self.angle_z = 0.0
        self.d_angle = math.radians(1)

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:
            # print(self.angle_x, self.angle_y)
            if keys[pygame.K_RIGHT]:
                self.angle_y -= self.d_angle
            if keys[pygame.K_LEFT]:
                self.angle_y += self.d_angle
            if keys[pygame.K_UP]:
                self.angle_x -= self.d_angle
            if keys[pygame.K_DOWN]:
                self.angle_x += self.d_angle
            if keys[pygame.K_q]:
                self.angle_z -= self.d_angle
            if keys[pygame.K_e]:
                self.angle_z += self.d_angle
        elif keys[pygame.K_LSHIFT]:
            if keys[pygame.K_RIGHT]:
                self.x += self.dx
            if keys[pygame.K_LEFT]:
                self.x -= self.dx
            if keys[pygame.K_UP]:
                self.z += self.dz
            if keys[pygame.K_DOWN]:
                self.z -= self.dz
        else:
            # print(self.x, self.y, self.z)
            if keys[pygame.K_RIGHT]:
                self.x -= self.dx
            if keys[pygame.K_LEFT]:
                self.x += self.dx
            if keys[pygame.K_UP]:
                self.y += self.dy
            if keys[pygame.K_DOWN]:
                self.y -= self.dy


camera = Camera(100, 200, -1000)