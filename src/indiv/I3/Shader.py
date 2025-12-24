import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import ctypes
import math
import random

# ==============================================================================
# 4. SHADER CLASS
# ==============================================================================
class Shader:
    def __init__(self, vs_src, fs_src):
        self.program = compileProgram(
            compileShader(vs_src, GL_VERTEX_SHADER),
            compileShader(fs_src, GL_FRAGMENT_SHADER)
        )

    def use(self): glUseProgram(self.program)
    def set_mat4(self, name, mat): glUniformMatrix4fv(glGetUniformLocation(self.program, name), 1, GL_TRUE, mat)
    def set_vec3(self, name, x, y=None, z=None):
        if y is None: glUniform3fv(glGetUniformLocation(self.program, name), 1, x)
        else: glUniform3f(glGetUniformLocation(self.program, name), x, y, z)
    def set_float(self, name, val): glUniform1f(glGetUniformLocation(self.program, name), val)
    def set_bool(self, name, val): glUniform1i(glGetUniformLocation(self.program, name), int(val))
    def set_int(self, name, val): glUniform1i(glGetUniformLocation(self.program, name), val)
    def destroy(self): glDeleteProgram(self.program)

    def setup():
        vs = """
        #version 330 core
        layout (location = 0) in vec3 aPos;
        layout (location = 1) in vec3 aNormal;
        layout (location = 2) in vec2 aTexCoord;
        layout (location = 3) in mat4 aInstanceMatrix;

        out vec3 FragPos;
        out vec3 Normal;
        out vec2 TexCoord;

        uniform mat4 model;
        uniform mat4 view;
        uniform mat4 projection;
        uniform bool isInstanced;

        void main() {
            mat4 currentModel = isInstanced ? aInstanceMatrix : model;
            FragPos = vec3(currentModel * vec4(aPos, 1.0));
            Normal = mat3(transpose(inverse(currentModel))) * aNormal;
            TexCoord = aTexCoord;
            gl_Position = projection * view * vec4(FragPos, 1.0);
        }
        """

        fs = """
        #version 330 core
        out vec4 FragColor;
        in vec3 FragPos;
        in vec3 Normal;
        in vec2 TexCoord;

        uniform vec3 viewPos;
        uniform float alpha;
        uniform vec3 emissiveColor;

        uniform sampler2D diffuseMap;
        uniform sampler2D emissiveMap;
        uniform sampler2D lightMap;

        uniform bool useEmissive;
        uniform bool useLightMap;
        uniform vec3 tintColor;

        uniform vec3 spotPos;
        uniform vec3 spotDir;
        uniform float spotCutoff;

        vec3 lightDir = normalize(vec3(0.5, -1.0, 0.5));
        vec3 lightColor = vec3(1.0, 1.0, 0.9);

        void main() {
            vec4 texColor = texture(diffuseMap, TexCoord) * vec4(tintColor, 1.0);
            // vec3 bakedLight = texture(lightMap, TexCoord2).rgb;

            vec3 norm = normalize(Normal);
            vec3 finalColor;

            // Light Map
            if (useLightMap) {
                vec3 bakedLight = texture(lightMap, TexCoord).rgb;

                // Базовое освещение из lightmap
                finalColor = bakedLight * texColor.rgb;

                // Динамический spotlight (опционально)
                vec3 sLd = normalize(spotPos - FragPos);
                float theta = dot(sLd, normalize(-spotDir));
                if(theta > spotCutoff) {
                    float dist = length(spotPos - FragPos);
                    float att = 1.0 / (1.0 + 0.045 * dist + 0.0075 * dist * dist);
                    float spotIntensity = max(dot(norm, sLd), 0.0) * att * 0.5;
                    finalColor += vec3(1.0, 0.9, 0.7) * spotIntensity * texColor.rgb;
                }
            }
            else {
                vec3 ld = normalize(-lightDir);
                float diff = max(dot(norm, ld), 0.0);
                vec3 diffuse = diff * lightColor;

                vec3 viewDir = normalize(viewPos - FragPos);
                vec3 reflectDir = reflect(-ld, norm);
                float spec = pow(max(dot(viewDir, reflectDir), 0.0), 32);
                vec3 specular = 0.3 * spec * lightColor;
                vec3 ambient = 0.4 * lightColor;

                // Spotlight Logic
                vec3 sLd = normalize(spotPos - FragPos);
                float theta = dot(sLd, normalize(-spotDir));
                float spotIntensity = 0.0;
                if(theta > spotCutoff) {
                    float dist = length(spotPos - FragPos);
                    float att = 1.0 / (1.0 + 0.045 * dist + 0.0075 * dist * dist);
                    spotIntensity = max(dot(norm, sLd), 0.0) * 2.0 * att;
                }
                vec3 spotLightColor = vec3(1.0, 0.9, 0.7) * spotIntensity;

                vec3 lighting = (ambient + diffuse + specular + spotLightColor);
                finalColor = lighting * texColor.rgb + emissiveColor;
            }

            // EMISSIVE MAP (Fake Window Glow)
            if(useEmissive) {
                 vec3 lm = texture(emissiveMap, TexCoord).rgb;
                 // If the lightmap pixel is bright (window), add it
                 // if(lm.r > 0.9 && lm.g > 0.9) finalColor += lm * 0.6;
                 float brightness = dot(lm, vec3(0.299, 0.587, 0.114));
                 if(brightness > 0.5) {
                     finalColor += lm * brightness * 0.8;
                 }
            }

            FragColor = vec4(finalColor, alpha);
        }
        """

        return vs, fs