#include <cstdlib>
#include <cub/version.cuh>
#include <iostream>

int main() {
    std::cout << "CUB version: " << CUB_MAJOR_VERSION << "." << CUB_MINOR_VERSION << "."
              << CUB_SUBMINOR_VERSION << std::endl;
    return EXIT_SUCCESS;
}
