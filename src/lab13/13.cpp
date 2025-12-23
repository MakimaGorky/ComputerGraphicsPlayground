#include <SFML/Graphics.hpp>
#include <SFML/Window.hpp>
#include <SFML/System.hpp>
#include <GL/gl.h>
#include <bits/stdc++.h>

// ==========================================
// CONFIGURATION (GLOBALS)
// ==========================================
std::string SUN_MODEL_PATH = "sun.obj";
std::string PLANET_MODEL_PATH = "planet.obj";

// ==========================================
// MATH HELPERS
// ==========================================
constexpr float PI = 3.14159265f;

struct Vec3 {
    float x, y, z;
};

struct Vertex {
    Vec3 position;
    float u, v;
};

void setPerspective(float fov, float aspect, float zNear, float zFar) {
    float f = 1.0f / tan(fov * PI / 360.0f);
    float m[16] = {0};

    m[0] = f / aspect;
    m[5] = f;
    m[10] = (zFar + zNear) / (zNear - zFar);
    m[11] = -1.0f;
    m[14] = (2.0f * zFar * zNear) / (zNear - zFar);

    glMultMatrixf(m);
}

// ==========================================
// RESOURCE MANAGER & OBJ LOADER
// ==========================================

class Model {
public:
    std::vector<Vertex> vertices;
    GLuint displayListId;

    Model() : displayListId(0) {}
    ~Model() {
        if (displayListId) glDeleteLists(displayListId, 1);
    }

    bool loadFromFile(const std::string& filename) {
        std::ifstream file(filename);
        if (!file.is_open()) return false;

        std::vector<Vec3> temp_pos;
        std::vector<std::pair<float, float>> temp_uv;
        vertices.clear();

        std::string line;
        while (std::getline(file, line)) {
            std::stringstream ss(line);
            std::string prefix;
            ss >> prefix;

            if (prefix == "v") {
                Vec3 v;
                ss >> v.x >> v.y >> v.z;
                temp_pos.push_back(v);
            } else if (prefix == "vt") {
                float u, v;
                ss >> u >> v;
                temp_uv.push_back({u, v});
            } else if (prefix == "f") {
                std::string vertexStr;
                while (ss >> vertexStr) {
                    Vertex finalVert;
                    size_t slashPos = vertexStr.find('/');

                    int vIdx = std::stoi(vertexStr.substr(0, slashPos)) - 1;

                    size_t nextSlash = vertexStr.find('/', slashPos + 1);
                    int vtIdx = -1;
                    if (slashPos != std::string::npos && nextSlash != slashPos + 1) {
                        std::string vtStr = vertexStr.substr(slashPos + 1, nextSlash - slashPos - 1);
                        if(!vtStr.empty()) vtIdx = std::stoi(vtStr) - 1;
                    }

                    finalVert.position = temp_pos[vIdx];
                    if (vtIdx >= 0 && vtIdx < (int)temp_uv.size()) {
                        finalVert.u = temp_uv[vtIdx].first;
                        finalVert.v = temp_uv[vtIdx].second;
                    } else {
                        finalVert.u = 0; finalVert.v = 0;
                    }
                    vertices.push_back(finalVert);
                }
            }
        }

        // ВАЖНО: Нормализуем размер перед компиляцией
        normalize();

        compile();
        std::cout << "Successfully loaded and normalized: " << filename << " (" << vertices.size() << " vertices)\n";
        return true;
    }

private:
    // Функция нормализации размера модели
    void normalize() {
        if (vertices.empty()) return;

        // 1. Находим границы (Bounding Box)
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

        // 2. Находим центр
        float centerX = (minX + maxX) / 2.0f;
        float centerY = (minY + maxY) / 2.0f;
        float centerZ = (minZ + maxZ) / 2.0f;

        // 3. Находим максимальный размер (чтобы сохранить пропорции)
        float width = maxX - minX;
        float height = maxY - minY;
        float depth = maxZ - minZ;

        // Берем самую длинную сторону
        float maxDim = std::max({width, height, depth});
        if (maxDim == 0) return;

        // 4. Масштабируем так, чтобы самая длинная сторона стала равна 2.0 (от -1 до 1)
        float scaleFactor = 2.0f / maxDim;

        // 5. Применяем трансформацию ко всем вершинам
        for (auto& v : vertices) {
            v.position.x = (v.position.x - centerX) * scaleFactor;
            v.position.y = (v.position.y - centerY) * scaleFactor;
            v.position.z = (v.position.z - centerZ) * scaleFactor;
        }
    }

    void compile() {
        if (displayListId) glDeleteLists(displayListId, 1);
        displayListId = glGenLists(1);
        glNewList(displayListId, GL_COMPILE);
        glBegin(GL_TRIANGLES);
        for (const auto& v : vertices) {
            glTexCoord2f(v.u, v.v);
            glVertex3f(v.position.x, v.position.y, v.position.z);
        }
        glEnd();
        glEndList();
    }
};

// ==========================================
// CAMERA
// ==========================================

class Camera {
public:
    Vec3 position;
    Vec3 rotation;

    Camera() : position{0.f, 20.f, 50.f}, rotation{20.f, 0.f, 0.f} {}

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

        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::Left)) {
            rotation.y -= keyRotSpeed;
        }
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::Right)) {
            rotation.y += keyRotSpeed;
        }
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::Up)) {
            rotation.x -= keyRotSpeed;
        }
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::Down)) {
            rotation.x += keyRotSpeed;
        }

        if (rotation.x > 89.f) rotation.x = 89.f;
        if (rotation.x < -89.f) rotation.x = -89.f;

        float radYaw = rotation.y * PI / 180.0f;

        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::W)) {
            position.x += sin(radYaw) * moveSpeed;
            position.z -= cos(radYaw) * moveSpeed;
        }
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::S)) {
            position.x -= sin(radYaw) * moveSpeed;
            position.z += cos(radYaw) * moveSpeed;
        }
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::A)) {
            position.x -= cos(radYaw) * moveSpeed;
            position.z -= sin(radYaw) * moveSpeed;
        }
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::D)) {
            position.x += cos(radYaw) * moveSpeed;
            position.z += sin(radYaw) * moveSpeed;
        }
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::Space)) {
            position.y += moveSpeed;
        }
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::LShift)) {
            position.y -= moveSpeed;
        }
    }

    void applyTransform() {
        glRotatef(rotation.x, 1.f, 0.f, 0.f);
        glRotatef(rotation.y, 0.f, 1.f, 0.f);
        glTranslatef(-position.x, -position.y, -position.z);
    }
};

// ==========================================
// SCENE OBJECTS
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

    Vec3 rotationAxis;
    Vec3 position;
    float r, g, b;

    CelestialBody(std::shared_ptr<Model> m, sf::Texture* tex, float sc, float dist, float oSpeed, float sSpeed)
        : model(m), texture(tex), scale(sc), orbitRadius(dist), orbitSpeed(oSpeed), selfRotationSpeed(sSpeed),
          orbitAngle(0), selfAngle(0) {

        r = 0.5f + (rand() % 50) / 100.f;
        g = 0.5f + (rand() % 50) / 100.f;
        b = 0.5f + (rand() % 50) / 100.f;

        position.x = 0;
        position.y = 0;
        position.z = 0;

        rotationAxis.x = ((rand() % 200) - 100) / 100.0f;
        rotationAxis.y = ((rand() % 200) - 100) / 100.0f;
        rotationAxis.z = ((rand() % 200) - 100) / 100.0f;

        float len = sqrt(rotationAxis.x*rotationAxis.x + rotationAxis.y*rotationAxis.y + rotationAxis.z*rotationAxis.z);
        if (len > 0.001f) {
            rotationAxis.x /= len;
            rotationAxis.y /= len;
            rotationAxis.z /= len;
        } else {
            rotationAxis = {0.f, 1.f, 0.f};
        }
    }

    void update(float dt, bool rotateSelf) {
        orbitAngle += orbitSpeed * dt;
        if (rotateSelf) {
            selfAngle += selfRotationSpeed * dt;
        }
    }

    void draw(float cx, float cy, float cz, bool move) {
        glPushMatrix();

        if (move) {
            float px = cx + orbitRadius * cos(orbitAngle);
            float pz = cz + orbitRadius * sin(orbitAngle);
            position.x = px;
            position.z = pz;

            glRotatef(selfAngle, rotationAxis.x, rotationAxis.y, rotationAxis.z);
        }
        glTranslatef(position.x, position.y, position.z);

        glScalef(scale, scale, scale);

        glColor3f(r, g, b);
        sf::Texture::bind(texture);

        if (model) {
            glCallList(model->displayListId);
        }

        glPopMatrix();
    }
};

// ==========================================
// UTILS
// ==========================================

void createDummyAssets() {
    std::ofstream file("donut.obj");
    file << "# Generated Donut OBJ\n";

    int segments = 20;
    int sides = 15;
    float radius = 2.0f;
    float tubeRadius = 0.8f;

    for (int i = 0; i <= segments; ++i) {
        float theta = i * 2.0f * PI / segments;
        float cosTheta = cos(theta);
        float sinTheta = sin(theta);

        for (int j = 0; j <= sides; ++j) {
            float phi = j * 2.0f * PI / sides;
            float cosPhi = cos(phi);
            float sinPhi = sin(phi);

            float x = (radius + tubeRadius * cosPhi) * cosTheta;
            float y = (radius + tubeRadius * cosPhi) * sinTheta;
            float z = tubeRadius * sinPhi;

            float u = (float)i / segments;
            float v = (float)j / sides;

            file << "v " << x << " " << y << " " << z << "\n";
            file << "vt " << u << " " << v << "\n";
        }
    }

    for (int i = 0; i < segments; ++i) {
        for (int j = 0; j < sides; ++j) {
            int current = i * (sides + 1) + j + 1;
            int next = current + (sides + 1);

            file << "f " << current << "/" << current << " "
                 << next << "/" << next << " "
                 << (current + 1) << "/" << (current + 1) << "\n";

            file << "f " << next << "/" << next << " "
                 << (next + 1) << "/" << (next + 1) << " "
                 << (current + 1) << "/" << (current + 1) << "\n";
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
    settings.antiAliasingLevel = 4;

    sf::RenderWindow window(
        sf::VideoMode({1200, 800}),
        "SFML 3.0 Solar System",
        sf::Style::Default,
        sf::State::Windowed,
        settings
    );

    window.setVerticalSyncEnabled(true);

    glEnable(GL_DEPTH_TEST);
    glEnable(GL_TEXTURE_2D);
    glEnable(GL_CULL_FACE);

    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    setPerspective(60.0f, 1200.f/800.f, 0.1f, 500.0f);
    glMatrixMode(GL_MODELVIEW);

    // ==========================================
    // LOADING MODELS
    // ==========================================

    auto sunMesh = std::make_shared<Model>();
    std::cout << "Attempting to load Sun model: " << SUN_MODEL_PATH << std::endl;
    if (!sunMesh->loadFromFile(SUN_MODEL_PATH)) {
        std::cerr << "Failed to load " << SUN_MODEL_PATH << ". Using default (donut.obj)." << std::endl;
        sunMesh->loadFromFile("donut.obj");
    }

    std::shared_ptr<Model> planetMesh;

    if (SUN_MODEL_PATH == PLANET_MODEL_PATH) {
        planetMesh = sunMesh;
        std::cout << "Planet model path matches Sun model path. Reusing model data." << std::endl;
    } else {
        planetMesh = std::make_shared<Model>();
        std::cout << "Attempting to load Planet model: " << PLANET_MODEL_PATH << std::endl;
        if (!planetMesh->loadFromFile(PLANET_MODEL_PATH)) {
            std::cerr << "Failed to load " << PLANET_MODEL_PATH << ". Using default (donut.obj)." << std::endl;
            planetMesh->loadFromFile("donut.obj");
        }
    }

    sf::Texture asteroidTex = createSpaceTexture();

    CelestialBody sun(sunMesh, &asteroidTex, 6.0f, 0.0f, 0.0f, 0.5f);
    sun.r = 1.0f; sun.g = 0.8f; sun.b = 0.2f;

    std::vector<CelestialBody> planets;
    // Создаем планеты. Благодаря нормализации scale 0.8f гарантирует,
    // что планета будет чуть меньше единичного радиуса.
    // planets.emplace_back(planetMesh, &asteroidTex, 0.8f, 10.0f, 1.2f, 30.0f);
    // planets.emplace_back(planetMesh, &asteroidTex, 1.2f, 16.0f, 0.8f, 45.0f);
    // planets.emplace_back(planetMesh, &asteroidTex, 0.5f, 22.0f, 1.5f, 90.0f);
    // planets.emplace_back(planetMesh, &asteroidTex, 1.5f, 30.0f, 0.5f, 20.0f);
    // planets.emplace_back(planetMesh, &asteroidTex, 1.0f, 38.0f, 0.7f, 60.0f);
    // planets.emplace_back(planetMesh, &asteroidTex, 0.9f, 45.0f, 0.4f, 50.0f);

    planets.emplace_back(planetMesh, &asteroidTex, 2.8f, 10.0f, 1.2f, 30.0f);
    planets.emplace_back(planetMesh, &asteroidTex, 3.2f, 16.0f, 0.8f, 45.0f);
    planets.emplace_back(planetMesh, &asteroidTex, 2.5f, 22.0f, 1.5f, 90.0f);
    planets.emplace_back(planetMesh, &asteroidTex, 3.5f, 30.0f, 0.5f, 20.0f);
    planets.emplace_back(planetMesh, &asteroidTex, 3.0f, 38.0f, 0.7f, 60.0f);
    planets.emplace_back(planetMesh, &asteroidTex, 2.9f, 45.0f, 0.4f, 50.0f);

    Camera camera;
    sf::Clock clock;

    bool isRotationEnabled = true;
    bool isTimeEnabled = true;

    while (window.isOpen()) {
        float dt = clock.restart().asSeconds();

        while (const std::optional event = window.pollEvent()) {
            if (event->is<sf::Event::Closed>()) {
                window.close();
            }
            else if (const auto* keyPressed = event->getIf<sf::Event::KeyPressed>()) {
                if (keyPressed->code == sf::Keyboard::Key::Escape)
                    window.close();

                if (keyPressed->code == sf::Keyboard::Key::R) {
                    isRotationEnabled = !isRotationEnabled;
                    std::cout << "Rotation: " << (isRotationEnabled ? "ON" : "OFF") << std::endl;
                }
                if (keyPressed->code == sf::Keyboard::Key::F) {
                    isTimeEnabled = !isTimeEnabled;
                    std::cout << "Passage of Time: " << (isTimeEnabled ? "ON" : "OFF") << std::endl;
                }
            }
            else if (const auto* resized = event->getIf<sf::Event::Resized>()) {
                glViewport(0, 0, resized->size.x, resized->size.y);
                glMatrixMode(GL_PROJECTION);
                glLoadIdentity();
                setPerspective(60.0f, (float)resized->size.x / resized->size.y, 0.1f, 500.0f);
                glMatrixMode(GL_MODELVIEW);
            }
        }

        camera.update(dt, window);

        sun.update(dt, isRotationEnabled);
        for (auto& planet : planets) {
            planet.update(dt, isRotationEnabled);
        }

        glClearColor(0.1f, 0.1f, 0.15f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

        glLoadIdentity();
        camera.applyTransform();

        sun.draw(0, 0, 0, isTimeEnabled);

        for (auto& planet : planets) {
            planet.draw(0, 0, 0, isTimeEnabled);
        }

        window.display();
    }

    return 0;
}