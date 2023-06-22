#include <iostream>
#include <libraw/libraw.h>

int main() {
    std::cout << libraw_version() << "\n";
    return 0;
}
