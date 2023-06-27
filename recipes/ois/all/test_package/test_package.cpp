#include <iostream>

#include <ois/OIS.h>

int main() {
    std::cout << "OIS version: " << OIS::InputManager::getVersionNumber() << std::endl;
    return 0;
}
