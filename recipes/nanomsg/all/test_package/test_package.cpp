#include "nanomsg/nn.h"
#include <cstdlib>
#include <iostream>

int main(void) {
    void *msg = nn_allocmsg(32, 0);
    nn_freemsg(msg);

    return EXIT_SUCCESS;
}
