// SFML 3.0

// c++ solution.cpp -o app -lsfml-graphics -lsfml-window -lsfml-system -lGLEW -lGL && ./app

#include <bits/stdc++.h>
#include <GL/glew.h>
#include <SFML/Window.hpp>
#include <SFML/Graphics.hpp>
#include <SFML/OpenGL.hpp>
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>

// --- Шейдеры ---
const char* vertexShaderSource = R"(
    #version 330 core
    layout (location = 0) in vec3 aPos;
    layout (location = 1) in vec3 aColor;
    layout (location = 2) in vec2 aTexCoord;

    out vec3 ourColor;
    out vec2 TexCoord;

    uniform mat4 model;
    uniform mat4 view;
    uniform mat4 projection;

    void main() {
        gl_Position = projection * view * model * vec4(aPos, 1.0);
        ourColor = aColor;
        TexCoord = aTexCoord;
    }
)";

const char* fragmentShaderSource = R"(
    #version 330 core
    in vec3 ourColor;
    in vec2 TexCoord;
    out vec4 FragColor;

    uniform sampler2D texture1;
    uniform sampler2D texture2;

    // mode: 0 = градиент (цвет вершин), 1 = текстура + цвет, 2 = микс двух текстур
    uniform int mode;
    uniform float mixRatio; // Коэффициент смешивания

    void main() {
        if(mode == 0) {
            // Градиентный тетраэдр или круг
            FragColor = vec4(ourColor, 1.0);
        }
        else if (mode == 1) {
            vec4 texCol = texture(texture1, TexCoord);
            // Допустим, 0 - чистая текстура, 1 - чистый цвет (или умножение)
            // Для задачи сделаем интерполяцию
            FragColor = mix(texCol, texCol * vec4(ourColor, 1.0), mixRatio);
        }
        else if (mode == 2) {
            FragColor = mix(texture(texture1, TexCoord), texture(texture2, TexCoord), mixRatio);
        }
    }
)";

// Функция для компиляции шейдеров
GLuint createShaderProgram() {
    GLuint vertexShader = glCreateShader(GL_VERTEX_SHADER);
    glShaderSource(vertexShader, 1, &vertexShaderSource, NULL);
    glCompileShader(vertexShader);

    // Проверка ошибок VS
    GLint success;
    GLchar infoLog[512];
    glGetShaderiv(vertexShader, GL_COMPILE_STATUS, &success);
    if (!success) {
        glGetShaderInfoLog(vertexShader, 512, NULL, infoLog);
        std::cerr << "Vertex Shader Error: " << infoLog << std::endl;
    }

    GLuint fragmentShader = glCreateShader(GL_FRAGMENT_SHADER);
    glShaderSource(fragmentShader, 1, &fragmentShaderSource, NULL);
    glCompileShader(fragmentShader);

    // Проверка ошибок FS
    glGetShaderiv(fragmentShader, GL_COMPILE_STATUS, &success);
    if (!success) {
        glGetShaderInfoLog(fragmentShader, 512, NULL, infoLog);
        std::cerr << "Fragment Shader Error: " << infoLog << std::endl;
    }

    GLuint shaderProgram = glCreateProgram();
    glAttachShader(shaderProgram, vertexShader);
    glAttachShader(shaderProgram, fragmentShader);
    glLinkProgram(shaderProgram);

    glDeleteShader(vertexShader);
    glDeleteShader(fragmentShader);
    return shaderProgram;
}

// Перевод HSV в RGB
void hsv2rgb(float h, float s, float v, float& r, float& g, float& b) {
    float c = v * s;
    float x = c * (1 - std::abs(fmod(h / 60.0, 2) - 1));
    float m = v - c;
    if (h >= 0 && h < 60) { r = c; g = x; b = 0; }
    else if (h >= 60 && h < 120) { r = x; g = c; b = 0; }
    else if (h >= 120 && h < 180) { r = 0; g = c; b = x; }
    else if (h >= 180 && h < 240) { r = 0; g = x; b = c; }
    else if (h >= 240 && h < 300) { r = x; g = 0; b = c; }
    else { r = c; g = 0; b = x; }
    r += m; g += m; b += m;
}

// Генерация шахмат
GLuint generateTexture1() {
    sf::Image img;
    img.resize({256, 256});
    for(unsigned int x=0; x<256; x++) {
        for(unsigned int y=0; y<256; y++) {
            bool white = ((x / 32) + (y / 32)) % 2 == 0;
            img.setPixel({x, y}, white ? sf::Color::White : sf::Color::Blue);
        }
    }
    GLuint texID;
    glGenTextures(1, &texID);
    glBindTexture(GL_TEXTURE_2D, texID);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 256, 256, 0, GL_RGBA, GL_UNSIGNED_BYTE, img.getPixelsPtr());
    glGenerateMipmap(GL_TEXTURE_2D);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    return texID;
}

// Генерация текстуры (полоски)
GLuint generateTexture2() {
    sf::Image img;
    img.resize({256, 256});
    for(unsigned int x=0; x<256; x++) {
        for(unsigned int y=0; y<256; y++) {
            sf::Color col = (x % 32 < 16) ? sf::Color::Red : sf::Color::Yellow;
            img.setPixel({x, y}, col);
        }
    }
    GLuint texID;
    glGenTextures(1, &texID);
    glBindTexture(GL_TEXTURE_2D, texID);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 256, 256, 0, GL_RGBA, GL_UNSIGNED_BYTE, img.getPixelsPtr());
    glGenerateMipmap(GL_TEXTURE_2D);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    return texID;
}

int main() {
    sf::ContextSettings settings;
    settings.depthBits = 24;
    settings.majorVersion = 3;
    settings.minorVersion = 3;

    sf::Window window(sf::VideoMode({800, 800}), "OpenGL Tasks: Tetra, Cubes, Circle", sf::Style::Default, sf::State::Windowed, settings);
    window.setFramerateLimit(60);

    glewExperimental = GL_TRUE;
    if (glewInit() != GLEW_OK) {
        std::cerr << "GLEW Init Failed!" << std::endl;
        return -1;
    }

    glEnable(GL_DEPTH_TEST);

    GLuint shaderProgram = createShaderProgram();
    GLuint tex1 = generateTexture1();
    GLuint tex2 = generateTexture2();


    // 1. Тетраэдр (Вершины + Цвета)
    float tetraVertices[] = {
         0.0f,  0.5f,  0.0f,  1.0f, 0.0f, 0.0f,  0.0f, 0.0f,
        -0.5f, -0.5f,  0.5f,  0.0f, 1.0f, 0.0f,  0.0f, 0.0f,
         0.5f, -0.5f,  0.5f,  0.0f, 0.0f, 1.0f,  0.0f, 0.0f,
         0.0f, -0.5f, -0.5f,  1.0f, 1.0f, 0.0f,  0.0f, 0.0f
    };
    // Индексы для отрисовки 4 треугольников
    unsigned int tetraIndices[] = {
        0, 1, 2,
        0, 2, 3,
        0, 3, 1,
        1, 3, 2
    };

    // 2. Куб (Вершины + Цвета + UV)
    float cubeVertices[] = {
        -0.5f, -0.5f, -0.5f,  1.0f, 0.0f, 0.0f,  0.0f, 0.0f,
         0.5f, -0.5f, -0.5f,  0.0f, 1.0f, 0.0f,  1.0f, 0.0f,
         0.5f,  0.5f, -0.5f,  0.0f, 0.0f, 1.0f,  1.0f, 1.0f,
         0.5f,  0.5f, -0.5f,  0.0f, 0.0f, 1.0f,  1.0f, 1.0f,
        -0.5f,  0.5f, -0.5f,  1.0f, 1.0f, 0.0f,  0.0f, 1.0f,
        -0.5f, -0.5f, -0.5f,  1.0f, 0.0f, 0.0f,  0.0f, 0.0f,

        -0.5f, -0.5f,  0.5f,  1.0f, 0.0f, 1.0f,  0.0f, 0.0f,
         0.5f, -0.5f,  0.5f,  0.0f, 1.0f, 1.0f,  1.0f, 0.0f,
         0.5f,  0.5f,  0.5f,  1.0f, 1.0f, 1.0f,  1.0f, 1.0f,
         0.5f,  0.5f,  0.5f,  1.0f, 1.0f, 1.0f,  1.0f, 1.0f,
        -0.5f,  0.5f,  0.5f,  0.0f, 0.0f, 0.0f,  0.0f, 1.0f,
        -0.5f, -0.5f,  0.5f,  1.0f, 0.0f, 1.0f,  0.0f, 0.0f,

        -0.5f,  0.5f,  0.5f,  1.0f, 0.0f, 0.0f,  1.0f, 0.0f,
        -0.5f,  0.5f, -0.5f,  0.0f, 1.0f, 0.0f,  1.0f, 1.0f,
        -0.5f, -0.5f, -0.5f,  0.0f, 0.0f, 1.0f,  0.0f, 1.0f,
        -0.5f, -0.5f, -0.5f,  0.0f, 0.0f, 1.0f,  0.0f, 1.0f,
        -0.5f, -0.5f,  0.5f,  1.0f, 1.0f, 0.0f,  0.0f, 0.0f,
        -0.5f,  0.5f,  0.5f,  1.0f, 0.0f, 0.0f,  1.0f, 0.0f,

         0.5f,  0.5f,  0.5f,  1.0f, 0.0f, 1.0f,  1.0f, 0.0f,
         0.5f,  0.5f, -0.5f,  0.0f, 1.0f, 1.0f,  1.0f, 1.0f,
         0.5f, -0.5f, -0.5f,  1.0f, 1.0f, 1.0f,  0.0f, 1.0f,
         0.5f, -0.5f, -0.5f,  1.0f, 1.0f, 1.0f,  0.0f, 1.0f,
         0.5f, -0.5f,  0.5f,  0.0f, 0.0f, 0.0f,  0.0f, 0.0f,
         0.5f,  0.5f,  0.5f,  1.0f, 0.0f, 1.0f,  1.0f, 0.0f,

        -0.5f, -0.5f, -0.5f,  0.0f, 1.0f, 0.0f,  0.0f, 1.0f,
         0.5f, -0.5f, -0.5f,  1.0f, 0.0f, 0.0f,  1.0f, 1.0f,
         0.5f, -0.5f,  0.5f,  0.0f, 0.0f, 1.0f,  1.0f, 0.0f,
         0.5f, -0.5f,  0.5f,  0.0f, 0.0f, 1.0f,  1.0f, 0.0f,
        -0.5f, -0.5f,  0.5f,  1.0f, 1.0f, 0.0f,  0.0f, 0.0f,
        -0.5f, -0.5f, -0.5f,  0.0f, 1.0f, 0.0f,  0.0f, 1.0f,

        -0.5f,  0.5f, -0.5f,  1.0f, 0.0f, 0.0f,  0.0f, 1.0f,
         0.5f,  0.5f, -0.5f,  0.0f, 1.0f, 0.0f,  1.0f, 1.0f,
         0.5f,  0.5f,  0.5f,  0.0f, 0.0f, 1.0f,  1.0f, 0.0f,
         0.5f,  0.5f,  0.5f,  0.0f, 0.0f, 1.0f,  1.0f, 0.0f,
        -0.5f,  0.5f,  0.5f,  1.0f, 1.0f, 0.0f,  0.0f, 0.0f,
        -0.5f,  0.5f, -0.5f,  1.0f, 0.0f, 0.0f,  0.0f, 1.0f
    };

    // 3. Круг
    std::vector<float> circleVertices;
    // Центр (белый)
    circleVertices.insert(circleVertices.end(), {0.0f, 0.0f, 0.0f, 1.0f, 1.0f, 1.0f, 0.5f, 0.5f});
    int segments = 64;
    for(int i = 0; i <= segments; i++) {
        float angle = i * (360.0f / segments);
        float rad = glm::radians(angle);
        float x = cos(rad) * 0.5f;
        float y = sin(rad) * 0.5f;

        float r, g, b;
        hsv2rgb(angle, 1.0f, 1.0f, r, g, b);

        circleVertices.push_back(x);
        circleVertices.push_back(y);
        circleVertices.push_back(0.0f);

        circleVertices.push_back(r);
        circleVertices.push_back(g);
        circleVertices.push_back(b);

        circleVertices.push_back(0.0f);
        circleVertices.push_back(0.0f);
    }

    // --- VAO / VBO Setup ---
    GLuint VAOs[3], VBOs[3], EBO_Tetra;
    glGenVertexArrays(3, VAOs);
    glGenBuffers(3, VBOs);
    glGenBuffers(1, &EBO_Tetra);

    // Setup Tetra
    glBindVertexArray(VAOs[0]);
    glBindBuffer(GL_ARRAY_BUFFER, VBOs[0]);
    glBufferData(GL_ARRAY_BUFFER, sizeof(tetraVertices), tetraVertices, GL_STATIC_DRAW);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO_Tetra);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, sizeof(tetraIndices), tetraIndices, GL_STATIC_DRAW);
    // Pos
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 8 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);
    // Color
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 8 * sizeof(float), (void*)(3 * sizeof(float)));
    glEnableVertexAttribArray(1);

    // Setup Cube
    glBindVertexArray(VAOs[1]);
    glBindBuffer(GL_ARRAY_BUFFER, VBOs[1]);
    glBufferData(GL_ARRAY_BUFFER, sizeof(cubeVertices), cubeVertices, GL_STATIC_DRAW);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 8 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 8 * sizeof(float), (void*)(3 * sizeof(float)));
    glEnableVertexAttribArray(1);
    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 8 * sizeof(float), (void*)(6 * sizeof(float)));
    glEnableVertexAttribArray(2);

    // Setup Circle
    glBindVertexArray(VAOs[2]);
    glBindBuffer(GL_ARRAY_BUFFER, VBOs[2]);
    glBufferData(GL_ARRAY_BUFFER, circleVertices.size() * sizeof(float), circleVertices.data(), GL_STATIC_DRAW);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 8 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 8 * sizeof(float), (void*)(3 * sizeof(float)));
    glEnableVertexAttribArray(1);

    // Переменные состояния
    glm::vec3 tetraPos(0.0f, 0.0f, -3.0f);
    float colorMix = 0.5f;
    float texMix = 0.5f;
    glm::vec2 circleScale(1.0f, 1.0f);

    bool running = true;
    while (running) {
        while (std::optional<sf::Event> event = window.pollEvent()) {
            if (event->is<sf::Event::Closed>()) {
                running = false;
            }
        }

        // 1. Тетраэдр (Стрелки)
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::Left)) tetraPos.x -= 0.05f;
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::Right)) tetraPos.x += 0.05f;
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::Up)) tetraPos.y += 0.05f;
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::Down)) tetraPos.y -= 0.05f;

        // 2. Куб Цвет (Q/A)
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::Q)) colorMix += 0.01f;
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::A)) colorMix -= 0.01f;
        colorMix = glm::clamp(colorMix, 0.0f, 1.0f);

        // 3. Куб Текстуры (W/S)
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::W)) texMix += 0.01f;
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::S)) texMix -= 0.01f;
        texMix = glm::clamp(texMix, 0.0f, 1.0f);

        // 4. Круг Масштаб (I/K Y-axis, J/L X-axis)
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::J)) circleScale.x -= 0.01f;
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::L)) circleScale.x += 0.01f;
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::K)) circleScale.y -= 0.01f;
        if (sf::Keyboard::isKeyPressed(sf::Keyboard::Key::I)) circleScale.y += 0.01f;

        // --- Рендеринг ---
        glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

        glUseProgram(shaderProgram);

        // Получаем Uniforms
        GLint modelLoc = glGetUniformLocation(shaderProgram, "model");
        GLint viewLoc = glGetUniformLocation(shaderProgram, "view");
        GLint projLoc = glGetUniformLocation(shaderProgram, "projection");
        GLint modeLoc = glGetUniformLocation(shaderProgram, "mode");
        GLint mixLoc = glGetUniformLocation(shaderProgram, "mixRatio");

        // Установка текстурных юнитов
        glUniform1i(glGetUniformLocation(shaderProgram, "texture1"), 0);
        glUniform1i(glGetUniformLocation(shaderProgram, "texture2"), 1);
        glActiveTexture(GL_TEXTURE0); glBindTexture(GL_TEXTURE_2D, tex1);
        glActiveTexture(GL_TEXTURE1); glBindTexture(GL_TEXTURE_2D, tex2);

        auto windowSize = window.getSize();
        int w = windowSize.x;
        int h = windowSize.y;

        // --- 1. Top-Left: Градиентный тетраэдр ---
        glViewport(0, h/2, w/2, h/2);
        glUniform1i(modeLoc, 0); // Градиент

        glm::mat4 model = glm::mat4(1.0f);
        model = glm::translate(model, tetraPos);
        // Статический поворот для лучшего обзора
        model = glm::rotate(model, glm::radians(30.0f), glm::vec3(1.0f, 1.0f, 0.0f));

        glm::mat4 view = glm::translate(glm::mat4(1.0f), glm::vec3(0.0f, 0.0f, 0.0f));
        glm::mat4 proj = glm::perspective(glm::radians(45.0f), (float)(w/2)/(h/2), 0.1f, 100.0f);

        glUniformMatrix4fv(modelLoc, 1, GL_FALSE, glm::value_ptr(model));
        glUniformMatrix4fv(viewLoc, 1, GL_FALSE, glm::value_ptr(view));
        glUniformMatrix4fv(projLoc, 1, GL_FALSE, glm::value_ptr(proj));

        glBindVertexArray(VAOs[0]);
        glDrawElements(GL_TRIANGLES, 12, GL_UNSIGNED_INT, 0);

        // --- 2. Top-Right: Куб с текстурой и цветом ---
        glViewport(w/2, h/2, w/2, h/2);
        glUniform1i(modeLoc, 1);
        glUniform1f(mixLoc, colorMix);

        model = glm::mat4(1.0f);
        model = glm::translate(model, glm::vec3(0.0f, 0.0f, -3.0f));
        model = glm::rotate(model, glm::radians(45.0f), glm::vec3(1.0f, 1.0f, 0.0f));

        glUniformMatrix4fv(modelLoc, 1, GL_FALSE, glm::value_ptr(model));

        glBindVertexArray(VAOs[1]);
        glDrawArrays(GL_TRIANGLES, 0, 36);

        // --- 3. Bottom-Left: Градиентный круг ---
        glViewport(0, 0, w/2, h/2);
        glUniform1i(modeLoc, 0);

        model = glm::mat4(1.0f);
        model = glm::translate(model, glm::vec3(0.0f, 0.0f, -2.0f));
        model = glm::scale(model, glm::vec3(circleScale, 1.0f));

        glUniformMatrix4fv(modelLoc, 1, GL_FALSE, glm::value_ptr(model));

        glBindVertexArray(VAOs[2]);
        glDrawArrays(GL_TRIANGLE_FAN, 0, segments + 2);

        // --- 4. Bottom-Right: Куб 2 текстуры ---
        glViewport(w/2, 0, w/2, h/2);
        glUniform1i(modeLoc, 2);
        glUniform1f(mixLoc, texMix);

        model = glm::mat4(1.0f);
        model = glm::translate(model, glm::vec3(0.0f, 0.0f, -3.0f));
        static float rotation = 0.0f;
        rotation += 0.01f;
        model = glm::rotate(model, rotation, glm::vec3(0.5f, 1.0f, 0.0f));

        glUniformMatrix4fv(modelLoc, 1, GL_FALSE, glm::value_ptr(model));

        glBindVertexArray(VAOs[1]);
        glDrawArrays(GL_TRIANGLES, 0, 36);

        window.display();
    }

    glDeleteVertexArrays(3, VAOs);
    glDeleteBuffers(3, VBOs);
    glDeleteBuffers(1, &EBO_Tetra);
    glDeleteProgram(shaderProgram);
    glDeleteTextures(1, &tex1);
    glDeleteTextures(1, &tex2);

    return 0;
}