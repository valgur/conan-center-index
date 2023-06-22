#include <assert/assert/assert.hpp>
#include <cstdlib>
#include <iostream>

int main(void) {
    std::cout << "Testing libassert\n";

    try {
        VERIFY(1 != 1);
    } catch (...) {
        return EXIT_SUCCESS;
    }

    return EXIT_FAILURE;
}
