#include <nvtiff.h>
#include <stdio.h>
#include <stddef.h>

int main() {
    nvtiffStreamParseFromFile("", NULL);
    printf("nvTIFF version: %d.%d.%d.%d\n", NVTIFF_VER_MAJOR, NVTIFF_VER_MINOR, NVTIFF_VER_PATCH, NVTIFF_VER_BUILD);
}
