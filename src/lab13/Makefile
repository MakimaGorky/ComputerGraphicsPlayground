CXX = c++
CXXFLAFS = -std=c++17 -Wall -O2
LDFLAGS = -lsfml-graphics -lsfml-window -lsfml-system -lGL

TARGET = 13
SRC = 13.cpp

all: $(TARGET)

$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) $(SRC) -o $(TARGET) $(LDFLAGS)

clean:
	rm -f $(TARGET) donut.obj