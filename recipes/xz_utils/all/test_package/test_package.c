#include <lzma.h>
#include <stdio.h>
#include <stdlib.h>

int main() {
    printf("LZMA version %s\n", lzma_version_string());
    return EXIT_SUCCESS;
}
