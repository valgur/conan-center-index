#include <nanoflann.hpp>
#include <cstdio>

int main() {
    int major = (NANOFLANN_VERSION >> 8) & 0xF;
    int minor = (NANOFLANN_VERSION >> 4) & 0xF;
    int patch = NANOFLANN_VERSION & 0xF;
    printf("nanoflann version: %d.%d.%d\n", major, minor, patch);
}
