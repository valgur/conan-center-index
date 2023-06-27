#include "fpgen/fpgen.hpp"
#include <iostream>
#include <vector>

int main() {
    std::vector<int> vals = {0, 1, 2, 3};
    auto gen = fpgen::from(vals);

    for (auto &&val : gen) {
        std::cout << val << std::endl;
    }
    return 0;
}
