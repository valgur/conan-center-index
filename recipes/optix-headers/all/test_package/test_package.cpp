#include <optix.h>
#include <cstdio>


int main() {
    int major = OPTIX_VERSION / 10000;
    int minor = (OPTIX_VERSION / 100) % 100;
    int patch = OPTIX_VERSION % 100;
    printf("OptiX version: %d.%d.%d\n", major, minor, patch);
}
