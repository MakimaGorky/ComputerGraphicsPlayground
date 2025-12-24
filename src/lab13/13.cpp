#include <GL/glew.h> // ВАЖНО: GLEW должен быть подключен ДО SFML/OpenGL
#include <SFML/Graphics.hpp>
#include <SFML/Window.hpp>
#include <SFML/System.hpp>

// Библиотека GLM (стандарт для математики в современном OpenGL)
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>

#include <iostream>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include <memory>
#include <cmath>
#include <algorithm>
#include <optional>

// ==========================================
// SHADERS (GLSL)
// ==========================================

const char* vertexShaderSource = R"(
    #version 330 core
    layout (location = 0) in vec3 aPos;
    layout (location = 1) in vec2 aTexCoord;

    out vec2 TexCoord;

    uniform mat4 model;
    uniform mat4 view;
    uniform mat4 projection;

    void main() {
        gl_Position = projection * view * model * vec4(aPos, 1.0);
        TexCoord = aTexCoord;
    }
)";

const char* fragmentShaderSource = R"(
    #version 330 core
    out vec4 FragColor;

    in vec2 TexCoord;

    uniform sampler2D texture1;
    uniform vec3 objectColor;

    void main() {
        vec4 texColor = texture(texture1, TexCoord);
        FragColor = texColor;// * vec4(objectColor, 1.0);
    }
)";

// ==========================================
// SHADER CLASS
// ==========================================
class Shader {
public:
    GLuint ID;

    Shader(const char* vShaderCode, const char* fShaderCode) {
        GLuint vertex, fragment;
        GLint success;
        char infoLog[512];

        // Vertex Shader
        vertex = glCreateShader(GL_VERTEX_SHADER);
        glShaderSource(vertex, 1, &vShaderCode, NULL);
        glCompileShader(vertex);
        checkCompileErrors(vertex, "VERTEX");

        // Fragment Shader
        fragment = glCreateShader(GL_FRAGMENT_SHADER);
        glShaderSource(fragment, 1, &fShaderCode, NULL);
        glCompileShader(fragment);
        checkCompileErrors(fragment, "FRAGMENT");

        // Shader Program
        ID = glCreateProgram();
        glAttachShader(ID, vertex);
        glAttachShader(ID, fragment);
        glLinkProgram(ID);
        checkCompileErrors(ID, "PROGRAM");

        glDeleteShader(vertex);
        glDeleteShader(fragment);
    }

    void use() {
        glUseProgram(ID);
    }

    // Установка матриц (Uniforms)
    void setMat4(const std::string &name, const glm::mat4 &mat) const {
        glUniformMatrix4fv(glGetUniformLocation(ID, name.c_str()), 1, GL_FALSE, &mat[0][0]);
    }

    void setVec3(const std::string &name, float x, float y, float z) const {
        glUniform3f(glGetUniformLocation(ID, name.c_str()), x, y, z);
    }

    void setInt(const std::string &name, int value) const {
        glUniform1i(glGetUniformLocation(ID, name.c_str()), value);
    }

private:
    void checkCompileErrors(GLuint shader, std::string type) {
        GLint success;
        char infoLog[1024];
        if (type != "PROGRAM") {
            glGetShaderiv(shader, GL_COMPILE_STATUS, &success);
            if (!success) {
                glGetShaderInfoLog(shader, 1024, NULL, infoLog);
                std::cout << "ERROR::SHADER_COMPILATION_ERROR of type: " << type << "\n" << infoLog << "\n -- --------------------------------------------------- -- " << std::endl;
            }
        } else {
            glGetProgramiv(shader, GL_LINK_STATUS, &success);
            if (!success) {
                glGetProgramInfoLog(shader, 1024, NULL, infoLog);
                std::cout << "ERROR::PROGRAM_LINKING_ERROR of type: " << type << "\n" << infoLog << "\n -- --------------------------------------------------- -- " << std::endl;
            }
        }
    }
};

// ==========================================
// DATA STRUCTURES
// ==========================================
struct Vertex {
    glm::vec3 position;
    glm::vec2 texCoords;
};

// ==========================================
// MODEL / MESH LOADER
// ==========================================
class Model {
public:
    GLuint VAO, VBO;
    size_t vertexCount;

    Model() : VAO(0), VBO(0), vertexCount(0) {}

    ~Model() {
        if (VAO) glDeleteVertexArrays(1, &VAO);
        if (VBO) glDeleteBuffers(1, &VBO);
    }

    bool loadFromFile(const std::string& filename) {
        std::vector<Vertex> vertices;
        std::ifstream file(filename);
        if (!file.is_open()) return false;

        std::vector<glm::vec3> temp_pos;
        std::vector<glm::vec2> temp_uv;

        std::string line;
        while (std::getline(file, line)) {
            std::stringstream ss(line);
            std::string prefix;
            ss >> prefix;

            if (prefix == "v") {
                glm::vec3 v;
                ss >> v.x >> v.y >> v.z;
                temp_pos.push_back(v);
            } else if (prefix == "vt") {
                glm::vec2 v;
                ss >> v.x >> v.y;
                temp_uv.push_back(v);
            } else if (prefix == "f") {
                std::string vertexStr;
                std::vector<Vertex> polygonVertices;
                while (ss >> vertexStr) {
                    Vertex finalVert;
                    size_t slashPos = vertexStr.find('/');
                    int vIdx = std::stoi(vertexStr.substr(0, slashPos)) - 1;

                    size_t nextSlash = vertexStr.find('/', slashPos + 1);
                    int vtIdx = -1;
                    if (slashPos != std::string::npos && nextSlash != slashPos + 1) {
                        std::string vtStr = vertexStr.substr(slashPos + 1, nextSlash - slashPos - 1);
                        if (!vtStr.empty()) vtIdx = std::stoi(vtStr) - 1;
                    }

                    finalVert.position = temp_pos[vIdx];
                    if (vtIdx >= 0 && vtIdx < (int)temp_uv.size()) {
                        finalVert.texCoords = temp_uv[vtIdx];
                    } else {
                        finalVert.texCoords = {0.0f, 0.0f};
                    }
                    polygonVertices.push_back(finalVert);
                }

                // Триангуляция (fan triangulation)
                for (size_t i = 2; i < polygonVertices.size(); ++i) {
                    vertices.push_back(polygonVertices[0]);
                    vertices.push_back(polygonVertices[i - 1]);
                    vertices.push_back(polygonVertices[i]);
                }
            }
        }

        normalize(vertices);
        setupMesh(vertices);
        std::cout << "Loaded: " << filename << " (" << vertices.size() << " vertices)\n";
        return true;
    }

private:
    void normalize(std::vector<Vertex>& vertices) {
        if (vertices.empty()) return;

        float minX = 1e9, minY = 1e9, minZ = 1e9;
        float maxX = -1e9, maxY = -1e9, maxZ = -1e9;

        for (const auto& v : vertices) {
            if (v.position.x < minX) minX = v.position.x;
            if (v.position.x > maxX) maxX = v.position.x;
            if (v.position.y < minY) minY = v.position.y;
            if (v.position.y > maxY) maxY = v.position.y;
            if (v.position.z < minZ) minZ = v.position.z;
            if (v.position.z > maxZ) maxZ = v.position.z;
        }

        float centerX = (minX + maxX) / 2.0f;
        float centerY = (minY + maxY) / 2.0f;
        float centerZ = (minZ + maxZ) / 2.0f;

        float maxDim = std::max({maxX - minX, maxY - minY, maxZ - minZ});
        if (maxDim == 0) return;
        float scaleFactor = 2.0f / maxDim;

        for (auto& v : vertices) {
            v.position.x = (v.position.x - centerX) * scaleFactor;
            v.position.y = (v.position.y - centerY) * scaleFactor;
            v.position.z = (v.position.z - centerZ) * scaleFactor;
        }
    }

    void setupMesh(const std::vector<Vertex>& vertices) {
        vertexCount = vertices.size();

        glGenVertexArrays(1, &VAO);
        glGenBuffers(1, &VBO);

        glBindVertexArray(VAO);

        glBindBuffer(GL_ARRAY_BUFFER, VBO);
        glBufferData(GL_ARRAY_BUFFER, vertices.size() * sizeof(Vertex), &vertices[0], GL_STATIC_DRAW);

        // Позиции вершин (layout 0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, sizeof(Vertex), (void*)0);
        glEnableVertexAttribArray(0);

        // Текстурные координаты (layout 1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, sizeof(Vertex), (void*)offsetof(Vertex, texCoords));
        glEnableVertexAttribArray(1);

        glBindVertexArray(0);
    }
};

// ==========================================
// CAMERA
// ==========================================
class Camera {
public:
    glm::vec3 position;
    glm::vec2 rotation; // x = pitch, y = yaw

    Camera() : position(0.0f, 20.0f, 50.0f), rotation(20.0f, 0.0f) {}

    void update(float dt, const sf::Window& window) {
        float moveSpeed = 30.0f * dt;
        float mouseSens = 0.12f;
        float keyRotSpeed = 80.0f * dt;

        if (sf::Mouse::isButtonPressed(sf::Mouse::Button::Right)) {
            sf::Vector2i center(window.getSize().x / 2, window.getSize().y / 2);
            sf::Vector2i mousePos = sf::Mouse::getPosition(window);
            sf::Vector2i delta = mousePos - center;

            rotation.y += delta.x * mouseSens;
            rotation.x += delta.y * mouseSens;

            sf::Mouse::setPosition(center, window);
        }

        // Keyboard rotation
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::Left)) rotation.y -= keyRotSpeed;
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::Right)) rotation.y += keyRotSpeed;
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::Up)) rotation.x -= keyRotSpeed;
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::Down)) rotation.x += keyRotSpeed;

        // Clamp Pitch
        if (rotation.x > 89.f) rotation.x = 89.f;
        if (rotation.x < -89.f) rotation.x = -89.f;

        // Movement
        float radYaw = glm::radians(rotation.y);
        glm::vec3 forward(sin(radYaw), 0.0f, -cos(radYaw));
        glm::vec3 right(cos(radYaw), 0.0f, sin(radYaw));

        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::W)) position += forward * moveSpeed;
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::S)) position -= forward * moveSpeed;
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::A)) position -= right * moveSpeed;
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::D)) position += right * moveSpeed;
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::Space)) position.y += moveSpeed;
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::LShift)) position.y -= moveSpeed;
    }

    glm::mat4 getViewMatrix() {
        glm::mat4 view = glm::mat4(1.0f);
        view = glm::rotate(view, glm::radians(rotation.x), glm::vec3(1.0f, 0.0f, 0.0f));
        view = glm::rotate(view, glm::radians(rotation.y), glm::vec3(0.0f, 1.0f, 0.0f));
        view = glm::translate(view, -position);
        return view;
    }
};

// ==========================================
// SCENE OBJECT
// ==========================================
class CelestialBody {
public:
    std::shared_ptr<Model> model;
    sf::Texture* texture;

    float scale;
    float orbitRadius;
    float orbitSpeed;
    float selfRotationSpeed;
    float orbitAngle;
    float selfAngle;

    glm::vec3 rotationAxis;
    glm::vec3 position;
    glm::vec3 color;

    CelestialBody(std::shared_ptr<Model> m, sf::Texture* tex, float sc, float dist, float oSpeed, float sSpeed)
        : model(m), texture(tex), scale(sc), orbitRadius(dist), orbitSpeed(oSpeed), selfRotationSpeed(sSpeed),
          orbitAngle(0), selfAngle(0) {

        color.r = 0.5f + (rand() % 50) / 100.f;
        color.g = 0.5f + (rand() % 50) / 100.f;
        color.b = 0.5f + (rand() % 50) / 100.f;

        position = glm::vec3(0.0f);

        rotationAxis.x = ((rand() % 200) - 100) / 100.0f;
        rotationAxis.y = ((rand() % 200) - 100) / 100.0f;
        rotationAxis.z = ((rand() % 200) - 100) / 100.0f;
        if (glm::length(rotationAxis) > 0.001f) rotationAxis = glm::normalize(rotationAxis);
        else rotationAxis = glm::vec3(0, 1, 0);
    }

    void update(float dt, bool rotateSelf) {
        orbitAngle += orbitSpeed * dt;
        if (rotateSelf) selfAngle += selfRotationSpeed * dt;
    }

    void draw(Shader& shader, float cx, float cz, bool move) {
        if (!model) return;

        glm::mat4 modelMat = glm::mat4(1.0f);

        if (move) {
            float px = cx + orbitRadius * cos(orbitAngle);
            float pz = cz + orbitRadius * sin(orbitAngle);
            position.x = px;
            position.z = pz;

            modelMat = glm::translate(modelMat, position);
            modelMat = glm::rotate(modelMat, glm::radians(selfAngle), rotationAxis);
        } else {
            modelMat = glm::translate(modelMat, position);
        }

        modelMat = glm::scale(modelMat, glm::vec3(scale));

        shader.setMat4("model", modelMat);
        shader.setVec3("objectColor", color.r, color.g, color.b);

        // Активация текстуры
        glActiveTexture(GL_TEXTURE0);
        sf::Texture::bind(texture); // SFML биндит на активный юнит
        shader.setInt("texture1", 0);

        glBindVertexArray(model->VAO);
        glDrawArrays(GL_TRIANGLES, 0, model->vertexCount);
        glBindVertexArray(0);
    }
};

// ==========================================
// UTILS
// ==========================================
void createDummyAssets() {
    std::ofstream file("donut.obj");
    int segments = 20, sides = 15;
    float radius = 2.0f, tubeRadius = 0.8f;
    float PI = 3.14159265f;

    for (int i = 0; i <= segments; ++i) {
        float theta = i * 2.0f * PI / segments;
        for (int j = 0; j <= sides; ++j) {
            float phi = j * 2.0f * PI / sides;
            float x = (radius + tubeRadius * cos(phi)) * cos(theta);
            float y = (radius + tubeRadius * cos(phi)) * sin(theta);
            float z = tubeRadius * sin(phi);
            file << "v " << x << " " << y << " " << z << "\n";
            file << "vt " << (float)i/segments << " " << (float)j/sides << "\n";
        }
    }
    for (int i = 0; i < segments; ++i) {
        for (int j = 0; j < sides; ++j) {
            int cur = i * (sides + 1) + j + 1;
            int nxt = cur + (sides + 1);
            file << "f " << cur << "/" << cur << " " << nxt << "/" << nxt << " " << (cur + 1) << "/" << (cur + 1) << "\n";
            file << "f " << nxt << "/" << nxt << " " << (nxt + 1) << "/" << (nxt + 1) << " " << (cur + 1) << "/" << (cur + 1) << "\n";
        }
    }
    file.close();
}

sf::Texture createSpaceTexture() {
    sf::Image img;
    img.resize({256, 256}, sf::Color::Black);
    for(unsigned int x=0; x<256; x++) {
        for(unsigned int y=0; y<256; y++) {
            int val = rand() % 255;
            if ((x/20 + y/20) % 2 == 0) val /= 2;
            img.setPixel({x, y}, sf::Color(val, val, val));
        }
    }
    sf::Texture tex;
    tex.loadFromImage(img);
    tex.generateMipmap();
    tex.setSmooth(true);
    return tex;
}

// ==========================================
// MAIN
// ==========================================
int main() {
    srand(time(0));
    createDummyAssets();

    sf::ContextSettings settings;
    settings.depthBits = 24;
    settings.majorVersion = 3; // OpenGL 3.3
    settings.minorVersion = 3;
    settings.attributeFlags = sf::ContextSettings::Core; // Core Profile

    sf::RenderWindow window(sf::VideoMode({1200, 800}), "Modern OpenGL Solar System", sf::Style::Default, sf::State::Windowed, settings);
    window.setVerticalSyncEnabled(true);

    // Инициализация GLEW
    glewExperimental = GL_TRUE;
    if (glewInit() != GLEW_OK) {
        std::cerr << "Failed to initialize GLEW" << std::endl;
        return -1;
    }

    glEnable(GL_DEPTH_TEST);
    // В Core Profile нет GL_TEXTURE_2D, это управляется шейдерами
    // glEnable(GL_CULL_FACE); // Можно включить, если модели правильные

    // Компиляция шейдеров
    Shader shader(vertexShaderSource, fragmentShaderSource);

    // Загрузка моделей
    auto sunMesh = std::make_shared<Model>();
    if (!sunMesh->loadFromFile("sun.obj")) sunMesh->loadFromFile("donut.obj");

    auto planetMesh = std::make_shared<Model>();
    if (!planetMesh->loadFromFile("planet.obj")) planetMesh->loadFromFile("donut.obj");

    sf::Texture asteroidTex; //= createSpaceTexture()
    std::string tex_path = "hell.jpg";
    sf::Image tex_img;
    tex_img.loadFromFile(tex_path);
    tex_img.flipVertically();
    asteroidTex.loadFromImage(tex_img);

    sf::Texture holoTex;
    tex_path = "hollow.jpg";
    tex_img.loadFromFile(tex_path);
    tex_img.flipVertically();
    holoTex.loadFromImage(tex_img);
    // sf::Texture holoTex = createSpaceTexture(); // Placeholder

    std::vector<CelestialBody> planets;
    planets.emplace_back(planetMesh, &asteroidTex, 2.8f, 10.0f, 1.2f, 30.0f);
    planets.emplace_back(planetMesh, &asteroidTex, 3.2f, 16.0f, 0.8f, 45.0f);
    planets.emplace_back(planetMesh, &asteroidTex, 2.5f, 22.0f, 1.5f, 90.0f);

    CelestialBody sun(sunMesh, &holoTex, 6.0f, 0.0f, 0.0f, 0.5f);

    Camera camera;
    sf::Clock clock;
    bool rotate = true;
    bool move = true;

    while (window.isOpen()) {
        float dt = clock.restart().asSeconds();

        while (const std::optional event = window.pollEvent()) {
            if (event->is<sf::Event::Closed>()) window.close();
            else if (const auto* key = event->getIf<sf::Event::KeyPressed>()) {
                if (key->code == sf::Keyboard::Key::Escape) window.close();
                if (key->code == sf::Keyboard::Key::R) rotate = !rotate;
                if (key->code == sf::Keyboard::Key::F) move = !move;
            }
            else if (const auto* resized = event->getIf<sf::Event::Resized>()) {
                glViewport(0, 0, resized->size.x, resized->size.y);
            }
        }

        camera.update(dt, window);
        sun.update(dt, rotate);
        for (auto& p : planets) p.update(dt, rotate);

        // Рендеринг
        glClearColor(0.1f, 0.1f, 0.15f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

        shader.use();

        // Матрица проекции
        glm::mat4 projection = glm::perspective(glm::radians(60.0f), (float)window.getSize().x / window.getSize().y, 0.1f, 500.0f);
        shader.setMat4("projection", projection);

        // Матрица вида (камера)
        glm::mat4 view = camera.getViewMatrix();
        shader.setMat4("view", view);

        // Отрисовка объектов
        sun.draw(shader, 0, 0, move);
        for (auto& p : planets) p.draw(shader, 0, 0, move);

        window.display();
    }

    return 0;
}