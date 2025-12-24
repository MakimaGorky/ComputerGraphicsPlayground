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

class Engine:
    def __init__(self, window_width, window_height, map_width, map_height):
        self.width, self.height = window_width, window_height
        self.map_width, self.map_depth = map_width, map_height

        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Airship Engine RC3: Complete")
        pygame.mouse.set_visible(False)
        self.clock = pygame.time.Clock()
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        try:
            self.heightmap_data = TextureUtils.load_heightmap_from_image(
            "assets/heightmap.png",
            self.map_width,
            self.map_depth
        )
            print('heightmap_data used!')
        except:
            self.heightmap_data = TextureUtils.generate_heightmap(self.map_width, self.map_depth)
            print('no heightmap_data found')

        self.setup_textures()
        self.setup_shaders()
        self.setup_geometry()
        self.setup_scene_instances()
        self.setup_npcs()

        self.airship_pos = np.array([0.0, 16.0, 0.0], dtype=np.float32)
        self.airship_yaw = -90.0
        self.airship_speed = 0.15
        self.turn_speed = 1.5

        self.clouds = self.create_clouds(15)
        self.spotlight_active = True
        self.packages = []

        self.camera = Camera(position=[0, 10, 20])

        self.running = True



    def setup_textures(self):
        # Fallback colors used if file not found
        self.tex_grass = Texture("assets/grass.jpg", gen_color=(30, 100, 30))
        self.tex_dirt = Texture("assets/dirt.jpg", gen_color=(100, 80, 50))
        self.tex_wood = Texture("assets/wood.jpg", gen_color=(139, 69, 19))
        self.tex_metal = Texture("assets/metal.jpg", gen_color=(150, 150, 160))
        self.tex_leaf = Texture("assets/leaf.jpg", gen_color=(20, 80, 20))
        self.tex_balloon = Texture("assets/cloth.jpg", gen_color=(200, 50, 50))
        # Special Maps
        self.tex_white = Texture(None, gen_color=(255, 255, 255))
        # self.tex_window = Texture(None, gen_color=(255, 255, 0)) # Yellow windows
        self.tex_window_emissive = self.create_window()

        print("Baking house lightmap...")
        house_lightmap_array = TextureUtils.create_house_lightmap()
        self.tex_house_lightmap = Texture(None, texture_type='lightmap', custom_array=house_lightmap_array)
        print("House lightmap complete!")

    def create_window(self):
        """Создаёт lightmap с паттерном окон"""
        arr = np.zeros((64, 64, 3), dtype=np.uint8)

        # Рисуем 4 "окна" на гранях куба
        # Окно на передней грани
        arr[20:30, 25:35] = [255, 255, 100]  # Тёплый свет

        # Можно добавить больше окон на разных участках UV-развёртки
        # В зависимости от того, как размечены UV-координаты куба

        return Texture(None, 'lightmap', gen_color=None, custom_array=arr)

    def bake_lightmap_for_terrain():
        """Запекает тени и освещение для terrain"""
        lightmap = np.ones((256, 256, 3)) * 0.4  # Базовое ambient

        # Симуляция солнечного света
        for y in range(256):
            for x in range(256):
                # Проверяем, в тени ли эта точка
                if is_in_shadow(x, y):
                    lightmap[y, x] *= 0.3  # Затемняем
                else:
                    lightmap[y, x] = [1.0, 0.95, 0.8]  # Солнечный свет

        return lightmap

    def setup_shaders(self):
        self.shader = Shader(*Shader.setup())

    def setup_geometry(self):
        t_v, t_i = GeometryUtils.generate_terrain_from_map(self.heightmap_data, 1.0, 1.0)
        self.terrain_mesh = Mesh(t_v, t_i)

        sph_v, sph_i = GeometryUtils.generate_sphere(1.0, 16, 16)
        self.sphere_mesh = Mesh(sph_v, sph_i)

        cube_v, cube_i = GeometryUtils.generate_cube_v_i()
        self.cube_mesh = Mesh(cube_v, cube_i)

        cyl_v, cyl_i = GeometryUtils.generate_cylinder(0.2, 1.0, 8)
        self.cyl_mesh = Mesh(cyl_v, cyl_i)

        cone_v, cone_i = GeometryUtils.generate_cone(0.8, 2.0, 8)
        self.cone_mesh = Mesh(cone_v, cone_i)

        pyr_v, pyr_i = GeometryUtils.generate_pyramid(1.2, 1.0)
        self.pyr_mesh = Mesh(pyr_v, pyr_i)

        rope_v, rope_i = GeometryUtils.generate_airship_ropes(3.5, 0.8, 0.5)
        self.rope_mesh = Mesh(rope_v, rope_i)

        str_v, str_i = GeometryUtils.generate_single_string(2.0)
        self.string_mesh = Mesh(str_v, str_i)

    def setup_npcs(self):
        self.npc_balloons = []
        for _ in range(5):
            self.npc_balloons.append({
                'pos': np.array([random.uniform(-40, 40), random.uniform(18, 25), random.uniform(-40, 40)]),
                'color': [random.random(), random.random(), random.random()],
                'speed': random.uniform(0.05, 0.1)
            })

    def create_clouds(self, count):
        clouds = []
        for _ in range(count):
            # Центр облака
            base_pos = np.array([
                random.uniform(-50, 50),
                random.uniform(12, 18),
                random.uniform(-50, 50)
            ])

            # Генерируем пушинки вокруг центра
            puffs = []
            num_puffs = random.randint(4, 8)
            for _ in range(num_puffs):
                offset = np.array([
                    random.uniform(-2.0, 2.0),
                    random.uniform(-1.0, 1.0),
                    random.uniform(-2.0, 2.0)
                ])
                scale = random.uniform(1.5, 3.5)
                puffs.append({'offset': offset, 'scale': scale})

            clouds.append({
                'pos': base_pos,
                'puffs': puffs,
                'flash_timer': 0,
                'speed': random.uniform(0.01, 0.04) # Облака теперь плывут
            })
        return clouds

    def get_mat(self, x, y, z, sx=1, sy=1, sz=1, ry=0):
        rad = np.radians(ry)
        c, s = np.cos(rad), np.sin(rad)
        rot = np.array([
            [c, 0, s, 0],
            [0, 1, 0, 0],
            [-s, 0, c, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        scale = np.array([
            [sx, 0, 0, 0],
            [0, sy, 0, 0],
            [0, 0, sz, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        trans = np.array([
            [1, 0, 0, x],
            [0, 1, 0, y],
            [0, 0, 1, z],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        return np.dot(trans, np.dot(rot, scale))

    def get_height_at(self, x, z):
        offset_x = - (self.map_width * 1.0) / 2.0
        offset_z = - (self.map_depth * 1.0) / 2.0

        c = int(x - offset_x)
        r = int(z - offset_z)

        if 0 <= c < self.map_width and 0 <= r < self.map_depth:
            return self.heightmap_data[r, c] * 5.0
        return 0.0

    def setup_scene_instances(self):
        trunks, leaves, houses, roofs, self.rocks = [], [], [], [], []

        # Trees
        for _ in range(40):
            x, z = random.uniform(-25, 25), random.uniform(-25, 25)
            # Avoid center
            if abs(x) < 3 and abs(z) < 3: continue

            y = self.get_height_at(x, z)
            trunks.append(self.get_mat(x, y, z))
            leaves.append(self.get_mat(x, y+1, z))

        # Houses (Base + Roof)
        for _ in range(8):
            x, z = random.uniform(-20, 20), random.uniform(-20, 20)
            if abs(x) < 4 and abs(z) < 4: continue

            y = self.get_height_at(x, z)
            houses.append(self.get_mat(x, y+0.5, z))
            roofs.append(self.get_mat(x, y+1.0, z))

        # Rocks
        for _ in range(20):
            x, z = random.uniform(-28, 28), random.uniform(-28, 28)
            y = self.get_height_at(x, z)
            self.rocks.append(self.get_mat(x, y+0.2, z, 0.8, 0.3, 0.8, random.uniform(0, 360)))

        self.cyl_mesh.init_instancing(trunks)
        self.cone_mesh.init_instancing(leaves)
        self.cube_mesh.init_instancing(houses)
        self.pyr_mesh.init_instancing(roofs)
        self.sphere_mesh.init_instancing(self.rocks)

    def process_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]: self.airship_yaw += self.turn_speed
        if keys[pygame.K_d]: self.airship_yaw -= self.turn_speed

        rad = np.radians(self.airship_yaw)
        forward = np.array([np.cos(rad), 0, np.sin(rad)])

        if keys[pygame.K_w]: self.airship_pos += forward * self.airship_speed
        if keys[pygame.K_s]: self.airship_pos -= forward * self.airship_speed

        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: self.running = False
                if event.key == pygame.K_SPACE:
                    self.packages.append({'pos': self.airship_pos + np.array([0,-1.5,0]), 'vel': 0.0})
                if event.key == pygame.K_f:
                    self.spotlight_active = not self.spotlight_active

    def update_physics(self):
        for npc in self.npc_balloons:
            npc['pos'][0] += npc['speed']
            if npc['pos'][0] > 40: npc['pos'][0] = -40

        for c in self.clouds:
            if c['flash_timer'] > 0: c['flash_timer'] -= 1
            else:
                if random.random() < 0.005: c['flash_timer'] = random.randint(5, 15)

        for p in self.packages:
            p['vel'] += 0.01
            p['pos'][1] -= p['vel']
            ty = self.get_height_at(p['pos'][0], p['pos'][2])
            if p['pos'][1] < ty + 0.25:
                p['pos'][1] = ty + 0.25
                p['vel'] = 0

    def draw_scene(self):
        # Update Uniforms
        self.shader.set_mat4("view", self.camera.get_view_matrix())
        self.shader.set_mat4("projection", self.camera.get_projection_matrix(self.width, self.height))
        self.shader.set_vec3("viewPos", self.camera.position)
        self.shader.set_vec3("spotPos", self.airship_pos)
        self.shader.set_vec3("spotDir", 0.0, -1.0, 0.0)
        self.shader.set_float("spotCutoff", np.cos(np.radians(15.5)) if self.spotlight_active else 1.1)

        # Reset Texture Defaults
        self.shader.set_vec3("tintColor", 1, 1, 1)
        self.shader.set_bool("useEmissive", False)
        self.shader.set_bool("useLightMap", False)

        self.tex_white.bind(1)
        self.shader.set_int("emissiveMap", 1)
        self.shader.set_int("lightMap", 2)
        self.shader.set_int("diffuseMap", 0)

        # 1. Terrain
        self.tex_grass.bind(0)
        self.shader.set_mat4("model", np.identity(4, dtype=np.float32))
        self.terrain_mesh.draw(self.shader)

        # 2. Scenery Instances
        self.tex_wood.bind(0)
        self.cyl_mesh.draw_instanced(self.shader) # Trunks

        self.tex_leaf.bind(0)
        self.cone_mesh.draw_instanced(self.shader) # Leaves

        # Houses (Base) with Lightmap
        self.shader.set_bool("useEmissive", False)
        self.shader.set_bool("useLightMap", True)

        self.tex_wood.bind(0)
        self.tex_window_emissive.bind(1)
        self.tex_house_lightmap.bind(2)
        self.cube_mesh.draw_instanced(self.shader)
        self.shader.set_bool("useEmissive", False)
        self.shader.set_bool("useLightMap", False)

        # self.tex_white.bind(1)

        # Roofs (Red tint)
        self.tex_wood.bind(0)
        self.shader.set_vec3("tintColor", 1.0, 0.4, 0.4)
        self.pyr_mesh.draw_instanced(self.shader)
        self.shader.set_vec3("tintColor", 1, 1, 1)

        # Rocks
        self.tex_dirt.bind(0)
        self.sphere_mesh.draw_instanced(self.shader)

        # 3. Christmas Tree (Unique Object)
        ct_h = self.get_height_at(0, 0)
        self.tex_wood.bind(0)
        self.shader.set_mat4("model", self.get_mat(0, ct_h, 0, 1, 2, 1))
        self.cyl_mesh.draw(self.shader)

        self.tex_leaf.bind(0)
        # Stacked Cones
        self.shader.set_mat4("model", self.get_mat(0, ct_h + 1.5, 0, 2.5, 2.5, 2.5))
        self.cone_mesh.draw(self.shader)
        self.shader.set_mat4("model", self.get_mat(0, ct_h + 3.0, 0, 2.0, 2.0, 2.0))
        self.cone_mesh.draw(self.shader)
        self.shader.set_mat4("model", self.get_mat(0, ct_h + 4.5, 0, 1.5, 1.5, 1.5))
        self.cone_mesh.draw(self.shader)

        # 4. Airship
        # Balloon
        self.tex_balloon.bind(0)
        self.shader.set_vec3("tintColor", 1.0, 0.2, 0.2)
        balloon_y_offset = 1.0
        rope_y_offset = 0.4
        self.shader.set_mat4("model", self.get_mat(
            self.airship_pos[0], self.airship_pos[1] + balloon_y_offset - rope_y_offset, self.airship_pos[2],
            2.0, 2.0, 2.0, self.airship_yaw))
        self.sphere_mesh.draw(self.shader)

        # Ropes
        self.tex_metal.bind(0)
        self.shader.set_vec3("tintColor", 0.8, 0.8, 0.7)
        # Веревки рисуются от центра шара вниз, поэтому позиция та же, что у шара, но без скейла
        rope_model = self.get_mat(
            self.airship_pos[0], self.airship_pos[1] + balloon_y_offset, self.airship_pos[2],
            1.0, 1.0, 1.0, self.airship_yaw)
        self.shader.set_mat4("model", rope_model)
        self.rope_mesh.draw(self.shader)

        # Gondola
        self.tex_wood.bind(0)
        self.shader.set_vec3("tintColor", 1, 1, 1)
        gondola_y = self.airship_pos[1] + balloon_y_offset - 4.8
        self.shader.set_mat4("model", self.get_mat(
            self.airship_pos[0], gondola_y, self.airship_pos[2],
            1.0, 1.0, 1.0, self.airship_yaw))
        self.cube_mesh.draw(self.shader)

        # 5. NPCs
        self.tex_balloon.bind(0)
        for npc in self.npc_balloons:
            self.shader.set_vec3("tintColor", npc['color'][0], npc['color'][1], npc['color'][2])
            self.shader.set_mat4("model", self.get_mat(
                npc['pos'][0], npc['pos'][1] + 0.0, npc['pos'][2], 1.5, 1.5, 1.5))
            self.sphere_mesh.draw(self.shader)
        # self.shader.set_vec3("tintColor", 1, 1, 1)

            self.tex_white.bind(0)
            self.shader.set_vec3("tintColor", 0.9, 0.9, 0.9)
            # Масштабируем веревки по Y (0.75), чтобы они были короче для NPC
            self.shader.set_mat4("model", self.get_mat(
                npc['pos'][0], npc['pos'][1], npc['pos'][2], 1.0, 1.0, 1.0))
            self.string_mesh.draw(self.shader)
        self.shader.set_vec3("tintColor", 1, 1, 1)

        # 6. Packages
        self.tex_metal.bind(0)
        for p in self.packages:
            self.shader.set_mat4("model", self.get_mat(p['pos'][0], p['pos'][1], p['pos'][2], 0.5, 0.5, 0.5))
            self.cube_mesh.draw(self.shader)

        # 7. Transparent Clouds
        glDepthMask(GL_FALSE)
        self.tex_white.bind(0)
        for c in self.clouds:
            if c['flash_timer'] > 0:
                self.shader.set_vec3("emissiveColor", 0.8, 0.8, 0.9)
                alpha = 0.9
            else:
                self.shader.set_vec3("emissiveColor", 0.1, 0.1, 0.1)
                alpha = 0.5

            self.shader.set_float("alpha", alpha)
            for puff in c['puffs']:
                px = c['pos'][0] + puff['offset'][0]
                py = c['pos'][1] + puff['offset'][1]
                pz = c['pos'][2] + puff['offset'][2]
                s = puff['scale']

                self.shader.set_mat4("model", self.get_mat(px, py, pz, s, s, s))
                self.sphere_mesh.draw(self.shader)
            # self.shader.set_mat4("model", self.get_mat(
            #     c['pos'][0], c['pos'][1], c['pos'][2], c['scale'], c['scale'], c['scale']))
            # self.sphere_mesh.draw(self.shader)

        self.shader.set_float("alpha", 1.0)
        self.shader.set_vec3("emissiveColor", 0, 0, 0)
        glDepthMask(GL_TRUE)

    def update(self):
        self.process_input()
        self.update_physics()
        self.camera.follow(self.airship_pos, self.airship_yaw)

        glClearColor(0.1, 0.1, 0.15, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.shader.use()
        self.draw_scene()

        pygame.display.flip()
        self.clock.tick(60)

    def destroy(self):
        self.shader.destroy()
        self.terrain_mesh.destroy()
        self.sphere_mesh.destroy()
        self.cube_mesh.destroy()
        self.cyl_mesh.destroy()
        self.cone_mesh.destroy()
        self.pyr_mesh.destroy()
        self.rope_mesh.destroy()
        self.string_mesh.destroy()
        pygame.quit()