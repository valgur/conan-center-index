#include <bzlib.h>
#include <stdio.h>

int main() {
    char buffer [256] = {0};
    unsigned int size = 256;
    const char* version = BZ2_bzlibVersion();
    printf("Bzip2 version: %s\n", version);
    BZ2_bzBuffToBuffCompress(buffer, &size, "conan-package-manager", 21, 1, 0, 1);
}
