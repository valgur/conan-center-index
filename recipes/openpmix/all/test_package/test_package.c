#include <pmix.h>
#include <stdio.h>

int main(int argc, char **argv) {
    printf("PMIx has already been initialized: %d\n", PMIx_Initialized());
    return 0;
}
