#include <iostream>
#include <json/json.h>

int main(int argc, char **argv) {
    Json::Value value("Hello, World");
    std::cout << value.asString() << std::endl;
    return 0;
}
