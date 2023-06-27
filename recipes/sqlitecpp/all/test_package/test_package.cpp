#include <SQLiteCpp/SQLiteCpp.h>
#include <cstdlib>
#include <iostream>

int main() {
    std::cout << "SQLite3 version " << SQLite::VERSION << " (" << SQLite::getLibVersion() << ")"
              << std::endl;
    return EXIT_SUCCESS;
}
