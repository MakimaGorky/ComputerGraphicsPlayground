import sys
import os

# --- PRE-LAUNCH SETUP ---
# Fix for potential Gtk/Wayland issues on Linux
os.environ['SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR'] = '0'

try:
    import pygame
    from pygame.locals import *
    from OpenGL.GL import *
    from OpenGL.GL.shaders import compileProgram, compileShader
    import numpy as np
    import math
    import ctypes
    import random
except ImportError as e:
    print(f"CRITICAL ERROR: Missing libraries.\n{e}")
    print("Run: pip install PyOpenGL PyOpenGL_accelerate pygame numpy")
    sys.exit(1)

# =============================================================================
# 1. DEBUG & DIAGNOSTICS UTILS
# =============================================================================
class DebugPipeline:
    @staticmethod
    def log(stage, msg):
        print(f"[{stage}] {msg}")

    @staticmethod
    def check_gl_error(tag=""):
        err = glGetError()
        if err != GL_NO_ERROR:
            DebugPipeline.log("GL_ERROR", f"Code {err} at {tag}")
            return False
        return True

    @staticmethod
    def run_diagnostics():
        print("\n=== STARTING DIAGNOSTIC PIPELINE ===")

        # 1. Context Check
        try:
            vendor = glGetString(GL_VENDOR).decode()
            renderer = glGetString(GL_RENDERER).decode()
            version = glGetString(GL_VERSION).decode()
            DebugPipeline.log("CONTEXT", f"GPU: {renderer}")
            DebugPipeline.log("CONTEXT", f"Vendor: {vendor}")
            DebugPipeline.log("CONTEXT", f"OpenGL Version: {version}")
        except Exception as e:
            DebugPipeline.log("CRITICAL", f"Failed to get GL Context info: {e}")
            return False

        # 2. Shader Compile Test
        test_v = """
        #version 330 core
        layout (location=0) in vec3 aPos;
        void main() { gl_Position = vec4(aPos, 1.0); }
        """
        test_f = """
        #version 330 core
        out vec4 FragColor;
        void main() { FragColor = vec4(1.0, 0.0, 0.0, 1.0); }
        """
        try:
            vs = compileShader(test_v, GL_VERTEX_SHADER)
            fs = compileShader(test_f, GL_FRAGMENT_SHADER)
            prog = compileProgram(vs, fs)
            glDeleteProgram(prog)
            DebugPipeline.log("SHADER", "Test shader compiled successfully.")
        except Exception as e:
            DebugPipeline.log("CRITICAL", f"Shader compilation failed: {e}")
            return False

        # 3. Math Check
        try:
            m = np.identity(4, dtype=np.float32)
            if m.shape != (4,4) or m[0][0] != 1.0:
                raise ValueError("NumPy sanity check failed")
            DebugPipeline.log("MATH", "NumPy matrix operations sane.")
        except Exception as e:
            DebugPipeline.log("CRITICAL", f"Math lib failure: {e}")
            return False

        print("=== DIAGNOSTICS PASSED ===\n")
        return True

# =============================================================================
# 2. MATH UTILITIES
# =============================================================================
class MathUtils:
    @staticmethod
    def normalize(v):
        norm = np.linalg.norm(v)
        return v if norm == 0 else v / norm

    @staticmethod
    def create_perspective(fov, aspect, near, far):
        f = 1.0 / math.tan(math.radians(fov) / 2)
        m = np.zeros((4, 4), dtype=np.float32)
        m[0, 0] = f / aspect
        m[1, 1] = f
        m[2, 2] = (far + near) / (near - far)
        m[2, 3] = -1.0
        m[3, 2] = (2 * far * near) / (near - far)
        return m

    @staticmethod
    def create_lookat(eye, target, up):
        z = MathUtils.normalize(eye - target)
        x = MathUtils.normalize(np.cross(up, z))
        y = np.cross(z, x)
        m = np.identity(4, dtype=np.float32)
        m[0, :3] = x
        m[1, :3] = y
        m[2, :3] = z
        m[0, 3] = -np.dot(x, eye)
        m[1, 3] = -np.dot(y, eye)
        m[2, 3] = -np.dot(z, eye)
        return m

    @staticmethod
    def create_transformation(pos, rot_deg, scale_vec):
        T = np.identity(4, dtype=np.float32)
        T[0:3, 3] = pos
        ry = math.radians(rot_deg[1])
        c, s = math.cos(ry), math.sin(ry)
        Ry = np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]], dtype=np.float32)
        S = np.identity(4, dtype=np.float32)
        S[0,0], S[1,1], S[2,2] = scale_vec
        return T @ Ry @ S

# =============================================================================
# 3. SHADER & MESH
# =============================================================================
VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;
layout (location = 3) in mat4 aInstanceMatrix;

uniform mat4 uView;
uniform mat4 uProjection;
uniform bool uUseInstance;
uniform mat4 uModel;

out vec3 FragPos;
out vec3 Normal;

void main() {
    mat4 modelMatrix = uUseInstance ? aInstanceMatrix : uModel;
    vec4 worldPos = modelMatrix * vec4(aPos, 1.0);
    FragPos = vec3(worldPos);
    Normal = mat3(transpose(inverse(modelMatrix))) * aNormal;
    gl_Position = uProjection * uView * worldPos;
}
"""

FRAGMENT_SHADER = """
#version 330 core
out vec4 FragColor;
in vec3 FragPos;
in vec3 Normal;

struct Material { vec3 ambient; vec3 diffuse; vec3 specular; float shininess; vec3 emissive; };
struct SpotLight { vec3 position; vec3 direction; float cutOff; float outerCutOff; float constant; float linear; float quadratic; vec3 ambient; vec3 diffuse; vec3 specular; };
struct DirLight { vec3 direction; vec3 ambient; vec3 diffuse; vec3 specular; };

uniform vec3 uViewPos;
uniform Material material;
uniform DirLight dirLight;
uniform SpotLight spotLight;
uniform bool uSpotLightOn;
uniform vec3 uFogColor;
uniform float uFogStart;
uniform float uFogEnd;
uniform float uAlpha;

void main() {
    vec3 norm = normalize(Normal);
    vec3 viewDir = normalize(uViewPos - FragPos);

    // Directional
    vec3 lightDir = normalize(-dirLight.direction);
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 ambient = dirLight.ambient * material.ambient;
    vec3 diffuse = dirLight.diffuse * diff * material.diffuse;
    vec3 result = ambient + diffuse; // Simple DirLight (no spec for perf)

    // Spotlight
    if (uSpotLightOn) {
        vec3 sDir = normalize(spotLight.position - FragPos);
        float theta = dot(sDir, normalize(-spotLight.direction));
        float epsilon = spotLight.cutOff - spotLight.outerCutOff;
        float intensity = clamp((theta - spotLight.outerCutOff) / epsilon, 0.0, 1.0);

        float dist = length(spotLight.position - FragPos);
        float att = 1.0 / (spotLight.constant + spotLight.linear * dist + spotLight.quadratic * (dist * dist));

        float sDiff = max(dot(norm, sDir), 0.0);
        vec3 sAmbient = spotLight.ambient * material.ambient;
        vec3 sDiffuse = spotLight.diffuse * sDiff * material.diffuse;

        result += (sAmbient + sDiffuse) * att * intensity;
    }

    result += material.emissive;

    // Fog
    float distance = length(uViewPos - FragPos);
    float fogFactor = clamp((distance - uFogStart) / (uFogEnd - uFogStart), 0.0, 1.0);
    vec3 finalColor = mix(result, uFogColor, fogFactor);

    FragColor = vec4(finalColor, uAlpha);
}
"""

class Shader:
    def __init__(self):
        try:
            self.prog = compileProgram(
                compileShader(VERTEX_SHADER, GL_VERTEX_SHADER),
                compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
            )
        except Exception as e:
            print("!!! SHADER COMPILE ERROR !!!")
            print(e)
            sys.exit(1)
        self.locs = {}

    def use(self):
        glUseProgram(self.prog)

    def get_loc(self, name):
        if name not in self.locs:
            self.locs[name] = glGetUniformLocation(self.prog, name)
        return self.locs[name]

    def set_mat4(self, name, val):
        glUniformMatrix4fv(self.get_loc(name), 1, GL_TRUE, val)
    def set_vec3(self, name, val):
        glUniform3fv(self.get_loc(name), 1, val)
    def set_float(self, name, val):
        glUniform1f(self.get_loc(name), val)
    def set_bool(self, name, val):
        glUniform1i(self.get_loc(name), int(val))

class Mesh:
    def __init__(self, verts, norms):
        self.v_count = len(verts) // 3
        v_data = np.array(verts, dtype=np.float32)
        n_data = np.array(norms, dtype=np.float32)

        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # VBO Pos
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, v_data.nbytes, v_data, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # VBO Norm
        self.nbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.nbo)
        glBufferData(GL_ARRAY_BUFFER, n_data.nbytes, n_data, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)

        # Instance VBO
        self.ibo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.ibo)
        stride = 64
        for i in range(4):
            loc = 3 + i
            glEnableVertexAttribArray(loc)
            glVertexAttribPointer(loc, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(i*16))
            glVertexAttribDivisor(loc, 1)

        glBindVertexArray(0)
        DebugPipeline.check_gl_error("Mesh Init")

    def update_instances(self, matrices):
        if not matrices: return
        data = np.array(matrices, dtype=np.float32).transpose(0, 2, 1).flatten()
        glBindBuffer(GL_ARRAY_BUFFER, self.ibo)
        glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_DYNAMIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def draw(self, shader, model_mat, instanced=False, count=0):
        glBindVertexArray(self.vao)
        if instanced and count > 0:
            shader.set_bool("uUseInstance", True)
            glDrawArraysInstanced(GL_TRIANGLES, 0, self.v_count, count)
        else:
            shader.set_bool("uUseInstance", False)
            shader.set_mat4("uModel", model_mat)
            glDrawArrays(GL_TRIANGLES, 0, self.v_count)
        glBindVertexArray(0)
        DebugPipeline.check_gl_error("Draw Call")

# =============================================================================
# 4. MAIN ENGINE
# =============================================================================
class GameEngine:
    def __init__(self):
        # 1. SETUP PYGAME WITH EXPLICIT GL ATTRIBUTES
        pygame.init()
        pygame.display.gl_set_attribute(GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(GL_CONTEXT_PROFILE_MASK, GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(GL_DEPTH_SIZE, 24)

        self.width, self.height = 1280, 720
        self.screen = pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Christmas Engine - Debug Build")

        # 2. RUN DIAGNOSTICS
        if not DebugPipeline.run_diagnostics():
            print("DIAGNOSTICS FAILED. Attempting to continue anyway...")

        # 3. INIT OPENGL STATE
        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # 4. LOAD ASSETS
        self.shader = Shader()
        self.cube = self.create_cube()
        self.floor = self.create_floor()

        # 5. SCENE STATE
        self.clock = pygame.time.Clock()
        self.cam_pos = np.array([0.0, 10.0, 20.0], dtype=np.float32)
        self.cam_yaw = 0.0
        self.emergency_mode = False

        # Generate World
        self.trees = []
        for i in range(20):
            x, z = random.uniform(-20,20), random.uniform(-20,20)
            self.trees.append(MathUtils.create_transformation([x, 0.5, z], [0,0,0], [0.5, 2.0, 0.5]))
        self.cube.update_instances(self.trees)

    def create_cube(self):
        # Simple Cube
        v = [-0.5,-0.5,-0.5, 0.5,-0.5,-0.5, 0.5,0.5,-0.5, 0.5,0.5,-0.5, -0.5,0.5,-0.5, -0.5,-0.5,-0.5,
             -0.5,-0.5,0.5, 0.5,-0.5,0.5, 0.5,0.5,0.5, 0.5,0.5,0.5, -0.5,0.5,0.5, -0.5,-0.5,0.5,
             -0.5,0.5,0.5, -0.5,0.5,-0.5, -0.5,-0.5,-0.5, -0.5,-0.5,-0.5, -0.5,-0.5,0.5, -0.5,0.5,0.5,
             0.5,0.5,0.5, 0.5,0.5,-0.5, 0.5,-0.5,-0.5, 0.5,-0.5,-0.5, 0.5,-0.5,0.5, 0.5,0.5,0.5,
             -0.5,-0.5,-0.5, 0.5,-0.5,-0.5, 0.5,-0.5,0.5, 0.5,-0.5,0.5, -0.5,-0.5,0.5, -0.5,-0.5,-0.5,
             -0.5,0.5,-0.5, 0.5,0.5,-0.5, 0.5,0.5,0.5, 0.5,0.5,0.5, -0.5,0.5,0.5, -0.5,0.5,-0.5]
        # Normals (Simplified)
        n = [0,0,-1]*6 + [0,0,1]*6 + [-1,0,0]*6 + [1,0,0]*6 + [0,-1,0]*6 + [0,1,0]*6
        return Mesh(v, n)

    def create_floor(self):
        v = [-50,0,-50, 50,0,-50, 50,0,50, 50,0,50, -50,0,50, -50,0,-50]
        n = [0,1,0]*6
        return Mesh(v, n)

    def draw_emergency_triangle(self):
        # If everything fails, this runs in fixed function pipeline (deprecated)
        # OR generic simple shader if Core Profile.
        # Since we are Core 3.3, we MUST use a shader.
        # We'll rely on clearing the screen to RED to prove life if render fails.
        glClearColor(1.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

    def run(self):
        print("Game Loop Started. Press F1 for Emergency Red Screen Test.")
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == QUIT: running = False
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE: running = False
                    if event.key == K_F1:
                        self.emergency_mode = not self.emergency_mode
                        print(f"Emergency Mode: {self.emergency_mode}")

            if self.emergency_mode:
                self.draw_emergency_triangle()
                pygame.display.flip()
                continue

            # Clear
            glClearColor(0.1, 0.1, 0.2, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            # Update Camera
            self.cam_yaw += 0.5 * dt
            # Orbit logic
            rad = 20.0
            cam_x = math.sin(self.cam_yaw) * rad
            cam_z = math.cos(self.cam_yaw) * rad

            view = MathUtils.create_lookat(np.array([cam_x, 10, cam_z]), np.array([0,0,0]), np.array([0,1,0]))
            proj = MathUtils.create_perspective(60, self.width/self.height, 0.1, 100.0)

            self.shader.use()
            self.shader.set_mat4("uView", view)
            self.shader.set_mat4("uProjection", proj)
            self.shader.set_vec3("uViewPos", [cam_x, 10, cam_z])

            # Light Defaults
            self.shader.set_vec3("dirLight.direction", [-0.5, -1.0, -0.5])
            self.shader.set_vec3("dirLight.ambient", [0.2, 0.2, 0.2])
            self.shader.set_vec3("dirLight.diffuse", [0.5, 0.5, 0.5])

            self.shader.set_bool("uSpotLightOn", False)
            self.shader.set_float("uAlpha", 1.0)
            self.shader.set_vec3("uFogColor", [0.1, 0.1, 0.2])
            self.shader.set_float("uFogStart", 20.0)
            self.shader.set_float("uFogEnd", 80.0)

            # Draw Floor
            self.shader.set_vec3("material.ambient", [0.2, 0.2, 0.2])
            self.shader.set_vec3("material.diffuse", [0.5, 0.5, 0.5])
            self.floor.draw(self.shader, np.identity(4))

            # Draw Trees (Instanced)
            self.shader.set_vec3("material.diffuse", [0.0, 1.0, 0.0])
            self.cube.draw(self.shader, None, instanced=True, count=20)

            pygame.display.flip()

        pygame.quit()

if __name__ == "__main__":
    GameEngine().run()