#include "c4/charconv.hpp"
#include "c4/std/std.hpp"

#include <iostream>

auto main() -> int {
    double value;
    c4::from_chars("52.4354", &value);

    std::cout << value << std::endl;

    return 0;
}
