#include "vo-amrwbenc/enc_if.h"
#include <stdlib.h>

int main(void) {
    void *state = E_IF_init();
    E_IF_exit(state);

    return EXIT_SUCCESS;
}
