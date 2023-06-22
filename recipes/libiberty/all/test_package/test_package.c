#include "libiberty/libiberty.h"
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    printf("GETPWD: %s\n", getpwd());
    printf("CONCAT (FOO + BAR): %s\n", concat("FOO", "BAR", NULL));
    return EXIT_SUCCESS;
}
