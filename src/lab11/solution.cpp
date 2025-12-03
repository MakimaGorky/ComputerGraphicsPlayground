// SFML 3.0

// c++ solution.cpp -o app -lsfml-graphics -lsfml-window -lsfml-system -lGLEW -lGL && ./app

#include <bits/stdc++.h>
#include <GL/glew.h>
#include <SFML/Window.hpp>
#include <SFML/Graphics.hpp>
#include <SFML/OpenGL.hpp>

// Шейдеры
const char* vertexShaderSource = R"(
    #version 330 core
    layout (location = 0) in vec2 aPos;
    layout (location = 1) in vec3 aColor;
    out vec3 vColor;
    void main() {
        gl_Position = vec4(aPos, 0.0, 1.0);
        vColor = aColor;
    }
)";

const char* fragmentShaderSource = R"(
    #version 330 core
    out vec4 FragColor;
    in vec3 vColor;
    uniform int uMode;
    uniform vec3 uUniformColor;
    void main() {
        if (uMode == 0) {
            // Режим 0: Константа (Оранжевый)
            FragColor = vec4(1.0, 0.5, 0.0, 1.0);
        }
        else if (uMode == 1) {
            // Режим 1: Uniform (Голубой)
            FragColor = vec4(uUniformColor, 1.0);
        }
        else {
            // Режим 2: Градиент (из вершин)
            FragColor = vec4(vColor, 1.0);
        }
    }
)";

GLuint createShaderProgram() {
    GLuint vertex = glCreateShader(GL_VERTEX_SHADER);
    glShaderSource(vertex, 1, &vertexShaderSource, NULL);
    glCompileShader(vertex);
    GLuint fragment = glCreateShader(GL_FRAGMENT_SHADER);
    glShaderSource(fragment, 1, &fragmentShaderSource, NULL);
    glCompileShader(fragment);
    GLuint program = glCreateProgram();
    glAttachShader(program, vertex);
    glAttachShader(program, fragment);
    glLinkProgram(program);
    glDeleteShader(vertex);
    glDeleteShader(fragment);
    return program;
}

int main() {
    sf::ContextSettings settings;
    settings.depthBits = 24;
    settings.majorVersion = 3;
    settings.minorVersion = 3;

    // Создание окна
    sf::Window window(
        sf::VideoMode({800, 600}),
        "OpenGL Shapes - Use Left/Right Arrows",
        sf::Style::Default,
        sf::State::Windowed,
        settings
    );
    window.setVerticalSyncEnabled(true);

    glewExperimental = GL_TRUE;
    if (glewInit() != GLEW_OK) return -1;

    // Геометрия
    std::vector<float> vertices;

    // 1. Четырехугольник
    vertices.insert(vertices.end(), {
        -0.9f, 0.9f, 1.0f, 0.0f, 0.0f,
        -0.9f, 0.4f, 0.0f, 1.0f, 0.0f,
        -0.4f, 0.9f, 0.0f, 0.0f, 1.0f,
        -0.4f, 0.4f, 1.0f, 1.0f, 0.0f
    });

    // 2. Веер
    float cx = 0.5f, cy = 0.65f, r = 0.25f;
    vertices.insert(vertices.end(), {cx, cy, 1.0f, 1.0f, 1.0f});
    for (int i = 0; i <= 5; ++i) {
        float a = i * (3.14159f / 5.0f);
        vertices.insert(vertices.end(), {cx + r * cos(a), cy + r * sin(a), (i%2==0?1.0f:0.0f), 0.0f, 1.0f});
    }

    // 3. Пятиугольник
    cx = 0.0f; cy = -0.5f; r = 0.3f;
    vertices.insert(vertices.end(), {cx, cy, 0.5f, 0.5f, 0.5f});
    for (int i = 0; i <= 5; ++i) {
        int cur_i = i % 5;
        float a = cur_i * (2.0f * 3.14159f / 5.0f) + (3.14159f / 2.0f);
        vertices.insert(vertices.end(), {cx + r * cos(a), cy + r * sin(a), (float)cur_i/5.0f, 1.0f-(float)cur_i/5.0f, 0.5f});
    }

    GLuint VBO, VAO;
    glGenVertexArrays(1, &VAO);
    glGenBuffers(1, &VBO);
    glBindVertexArray(VAO);
    glBindBuffer(GL_ARRAY_BUFFER, VBO);
    glBufferData(GL_ARRAY_BUFFER, vertices.size() * sizeof(float), vertices.data(), GL_STATIC_DRAW);

    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 5 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 5 * sizeof(float), (void*)(2 * sizeof(float)));
    glEnableVertexAttribArray(1);

    GLuint prog = createShaderProgram();
    glUseProgram(prog);

    GLint modeLoc = glGetUniformLocation(prog, "uMode");
    GLint colorLoc = glGetUniformLocation(prog, "uUniformColor");

    int currentMode = 0;
    std::cout << "Current Mode: 0 (Constant Color)" << std::endl;

    // Главный цикл
    while (window.isOpen()) {
        while (const std::optional event = window.pollEvent()) {
            if (event->is<sf::Event::Closed>()) {
                window.close();
            }
            // Обработка нажатий клавиш
            else if (const auto* keyEvent = event->getIf<sf::Event::KeyPressed>()) {
                bool modeChanged = false;

                // Стрелка ВПРАВО -> Следующий режим
                if (keyEvent->code == sf::Keyboard::Key::Right) {
                    currentMode = (currentMode + 1) % 3;
                    modeChanged = true;
                }
                // Стрелка ВЛЕВО -> Предыдущий режим
                else if (keyEvent->code == sf::Keyboard::Key::Left) {
                    currentMode--;
                    if (currentMode < 0) currentMode = 2;
                    modeChanged = true;
                }
                if (keyEvent->code == sf::Keyboard::Key::Escape) {
                    window.close();
                }

                if (modeChanged) {
                    std::cout << "Switched to Mode: " << currentMode;
                    if (currentMode == 0) std::cout << " (Constant)";
                    else if (currentMode == 1) std::cout << " (Uniform)";
                    else std::cout << " (Gradient)";
                    std::cout << std::endl;
                }
            }
        }

        // Отрисовка
        glClearColor(0.2f, 0.3f, 0.3f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);

        glUseProgram(prog);
        glUniform1i(modeLoc, currentMode);
        glUniform3f(colorLoc, 0.0f, 1.0f, 1.0f); // Cyan

        glBindVertexArray(VAO);

        // 1. Quad
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4);
        // 2. Fan
        glDrawArrays(GL_TRIANGLE_FAN, 4, 7);
        // 3. Pentagon
        glDrawArrays(GL_TRIANGLE_FAN, 11, 7);

        window.display();
    }

    // Очистка памяти
    glDeleteVertexArrays(1, &VAO);
    glDeleteBuffers(1, &VBO);
    glDeleteProgram(prog);

    return 0;
}