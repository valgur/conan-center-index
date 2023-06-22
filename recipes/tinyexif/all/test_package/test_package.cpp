#include "TinyEXIF.h"
#include <iostream>

int main() {
    TinyEXIF::EXIFInfo exif;

    std::cout << exif.Fields << std::endl;

    return 0;
}
