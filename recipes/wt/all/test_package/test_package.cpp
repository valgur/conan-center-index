#include <Wt/WEnvironment.h>
#include <cstdlib>
#include <iostream>

int main(void) {
    std::cout << "WT Library version: " << Wt::WEnvironment::libraryVersion() << std::endl;

    return EXIT_SUCCESS;
}
