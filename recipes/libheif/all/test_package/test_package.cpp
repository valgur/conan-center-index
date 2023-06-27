#include "libheif/heif.h"
#include <iostream>

int main() {
    std::cout << heif_get_version() << std::endl;
    return 0;
}
