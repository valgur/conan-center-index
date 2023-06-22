// LZ4 trivial example : print Library version number
// Copyright : Takayuki Matsuoka & Yann Collet

#include "lz4.h"
#include <stdio.h>

int main(int argc, char **argv) {
    (void)argc;
    (void)argv;
    printf("Hello World ! LZ4 Library version = %d\n", LZ4_versionNumber());
    return 0;
}
