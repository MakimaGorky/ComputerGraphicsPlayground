import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import ctypes
import math
import random

from Texture import *
from Geometry import *
from Camera import *
from Shader import *
from Mesh import *
from Engine import *


# ==============================================================================
# 6. APP CLASS
# ==============================================================================

class App:
    def __init__(self):
        self.width, self.height = 1000, 800

        self.map_width, self.map_depth = 600, 600

        self.engine = Engine(self.width, self.height, self.map_width, self.map_depth)

        self.running = self.engine.running

    def run(self):
        while self.running:
            self.engine.update()
            self.running = self.engine.running

        self.engine.destroy()

if __name__ == "__main__":
    app = App()
    app.run()