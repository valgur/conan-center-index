#include "test_package.cuh"

#include <iomanip>
#include <iostream>

int main(void) {
    std::cout << std::setprecision(3);
    std::cout << "pi is approximately " << estimate() << std::endl;
    return 0;
}
